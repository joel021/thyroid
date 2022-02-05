import large_image
import numpy as np
from tensorflow.keras.utils import to_categorical
import tensorflow as tf
import glob
from PIL import Image

from tensorflow.keras.preprocessing.image import ImageDataGenerator

# custom data-generator
# referencia: https://medium.com/analytics-vidhya/write-your-own-custom-data-generator-for-tensorflow-keras-1252b64e41c3
# x = numpy.shape(batch_size, input_height, input_width, input_channel)
# https://dzlab.github.io/dltips/en/keras/data-generator/

"""
Gera imagens de tamanho rxr a partir de um arquivo Whole Slide Imaging (WSI).
Os arquivos aceitos incluem mrxs e svs.

"""
class CustomDataset(tf.keras.utils.Sequence):
    def __init__(self, batch_size=64,
                 r=528,
                 path_files=None,
                 n_classes=2,
                 iterations=10,
                 netative_iterators = None,
                 test_mode = False,
                 path_positive=None):
        """
        :param batch_size: (int) tamanho do pacote. é o tanto de imagens por cada iteração de treinamento do modelo.
        :param r: (int) resolução da imagem de saída. rxr
        :param path_files: (list) de tupla (string, string) = (uri_file, classe). uri_file é o link completo do arquivo.
        classe é a classe correpondente.
        :param n_classes: numero de classes.
        :param iterations: este gerador consegue gerar infinitas imagens, então limite o numero de interações por epoca.
        """
        self.iterations = iterations
        self.path_files = path_files
        self.batch_size = batch_size
        self.i = 0  # posição do arquivo, que dá o iterator, não é a posição no iterator.
        self.r = r
        self.p = -1
        self.n_classes = n_classes
        self.test_mode = test_mode
        self.path_positive = path_positive
        self.p_positive = 0

        #inicialização
        if netative_iterators is None:
            self._instances_iterators()
            self.init_iterators()
        else:
            self.netative_iterators = netative_iterators

    """
    Para cada iterator p, itera-se até a primeira imagem válida
    """
    def init_iterators(self):

        for p in range(self.n_classes):
            print("Inicializando o iterator: {}, classe {}".format(p, self.netative_iterators[p][1]))
            self.p = p
            image_array = self._next()
            mean_rgb = np.mean(image_array[:, :, :4], axis=(0, 1))

            while self._not_content_RGBA(mean_rgb):
                image_array = self._next()
                mean_rgb = np.mean(image_array[:, :, :4], axis=(0, 1))
        print("Inicialização dos iterators completa.")
        self.p = -1 # posição do iterator na lista de iterators instanciados


    """
    Modificar uma instancia da posição p da lista de iterators
    Usada para alternar entre os arquivos sem perder a instancia do iterator
    """
    def _change_instance(self, p):

        if self.i < len(self.path_files) - 1:
            self.i = self.i + 1
            # se tiverem mais arquivos para serem lidos, acrescenta.
        else:
            # se não houverem mais arquivos, volta para o primeiro.
            self.i = 0

        ts = large_image.getTileSource(self.path_files[self.i][0])
        iterator = ts.tileIterator(
                tile_size=dict(width=self.r, height=self.r)
            )
        self.netative_iterators[p] = (iterator, self.path_files[self.i][1]) #tupla = (iterator,classe)

    """
    Criar a lista de iterators
    """
    def _instances_iterators(self):

        self.netative_iterators = []

        for i in range(self.n_classes):
            ts = large_image.getTileSource(self.path_files[self.i][0])

            iterator = ts.tileIterator(
                tile_size=dict(width=self.r, height=self.r)
            )
            self.netative_iterators.append((iterator, self.path_files[self.i][1])) #tupla = (iterator, classe)
            self.i = self.i + 1

        self.positive_iterator = glob.glob(self.path_positive+"/*.jpg")

    # return label encoder: [1,0,..,0] if cla=0, [0,1,...,0] if cla=1...
    def to_categorical(self, cla):
        return to_categorical(cla, num_classes=self.n_classes)

    def _not_content_RGBA(self, p):  # Tome RGB como três eixos ordenados. O A corresponde ao
        """
        Se a média dos valores RGB estão próximos de 1, então provavelmente são imagens
        em branco.
        Os pixels estão entre 0 e 1.
        """
        if self.test_mode:
            return False
        else:
            return (p[0] - 1) ** 2 + (p[1] - 1) ** 2 + (p[2] - 1) ** 2 <= 0.2 or (p[0]) ** 2 + (p[1]) ** 2 + (
            p[2]) ** 2 <= 0.2 or p[3] < 0.9

    """
    Pegar a proxima tile do arquivo. Se não houver, muda de arquivo.
    """
    def _next(self):
        try:
            image_array = next(self.netative_iterators[self.p][0])['tile'] / 255.
        except:
            #mudar a instancia do iterator da posição p para o do próximo arquivo disponível
            self._change_instance(self.p)
            image_array = next(self.netative_iterators[self.p][0])['tile'] / 255.

        return image_array

    def _next_item_i(self):

        #alternar entre os tipos de classes
        if self.p < self.n_classes - 1:
            self.p = self.p + 1
        else:
            self.p = 0

        X = list()
        Y = list()
        #obter uma imagem válida
        i = 0
        # imagens que têm nivel de transparência ou são quase totalmente preta ou
        # quase totalmente brancas não são inclusas
        while i < self.batch_size:
            image_array = self._next()
            mean_rgb = np.mean(image_array[:, :, :4], axis=(0, 1))

            if not self._not_content_RGBA(mean_rgb):
                image_array = image_array[:, :, :3]
                X.append(image_array)
                Y.append([0])
                i = i + 1

        return np.array(X), np.array(Y)

    def _next_positive(self):

        """
       Rotações e espelhamentos são aceitáveis como imagens geradas porque preservam a disposição dos componentes
       na imagem
       """

        data_generator = ImageDataGenerator(
            rotation_range=90,
            horizontal_flip=True,
            vertical_flip=True,
            fill_mode='nearest',
            zoom_range = 0.3,
            rescale= 1./255
        )

        i = 0

        uri_image = self.positive_iterator[self.p_positive]
        image_array = np.array(Image.open(uri_image))
        image_array = image_array.reshape((1,) + image_array.shape)
        X = []
        Y = []
        for image in data_generator.flow(image_array, batch_size=1):
            X.append(image[0])
            Y.append([1])

            i = i+1

            if i == self.batch_size:
                break

        if self.p_positive < len(self.positive_iterator):
            self.p_positive = self.p_positive + 1
        else:
            self.p_positive = 0

        return np.array(X), np.array(Y)
    """
    Extrai uma imagem válida do arquivo e cria bathc_size imagens e retorna uma tupla (X_batch,y_batch)
    """
    def __getitem__(self, index):

        if index % 2 == 0:
            return self._next_item_i()
        return self._next_positive()

    def __len__(self):
        # quantidade de batch
        return self.iterations

    def on_epoch_end(self):
        #Não é preciso reorganizar os dados.
        pass
