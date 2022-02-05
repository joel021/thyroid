"""
codigo encontrado em:

este codigo serve para gerar um arquivo tfrecord a partir de um arquivo csv.


Usage:
  # From tensorflow/models/
  # Create train data:
  python3 generate_tfrecord.py --csv_input=./train_labels.csv  --output_path=./train.record
  # Create validation data:
  python3 generate_tfrecord.py --csv_input=./test_labels.csv  --output_path=./validation.record
  # Create validation data
  python3 generate_tfrecord.py --csv_input=./validation_labels.csv  --output_path=./validation.record
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import io
import pandas as pd
import tensorflow as tf
from PIL import Image
from object_detection.utils import dataset_util
from collections import namedtuple

def split(df, group):
    data = namedtuple('data', ['filename', 'object'])
    gb = df.groupby(group)
    return [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]


def create_tf_example(group, path, label_map):
    """
    :param group: uma linha do csv associado as imagens: filename  width  height   class  xmin  ymin  xmax  ymax
    :param path: pasta onde estão todas as imagens
    :return: objeto padronizado para treinamento tf.train.Example
    """

    with tf.compat.v1.gfile.GFile(os.path.join(path, '{}'.format(group.filename)), 'rb') as fid: # abre a imagem correspondnete "filename", fid
        try:
            encoded_jpg = fid.read()
        except:
            print("Erro: "+group.filename)
            return None

    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)

    if image.format != 'JPEG':
        print("Não é jpeg")
        return

    width, height = image.size

    filename = group.filename.encode('utf8')

    image_format = b'jpg'
    classes_text = []
    classes = []

    for index, row in group.object.iterrows(): #uma anotação em um filename pode haver mais de um objeto, então percorre-se uma lista. No meu caso, a maioria tem apenas um objeto como anotação
        classes_text.append(row['class'].encode('utf8')) #insere o nome da classe
        classes.append(label_map[row['class']]) #insere o numero correspondente à classe

    #criar um objeto tf exemple padronizado por Tensorflow
    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/depth': dataset_util.int64_feature(3),
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))
    return tf_example

def generate_tfrecord(CSV_INPUT,IMAGE_DIR,OUTPUT_PATH, label_map):

    print(IMAGE_DIR)

    writer = tf.io.TFRecordWriter(OUTPUT_PATH)
    path = os.path.join(IMAGE_DIR)  # pasta onde estão todas as images associadas com o arquivo csv.
    examples = pd.read_csv(CSV_INPUT)  # csv associado com as imagens na pasta path
    grouped = split(examples, 'filename') #agrupa as linhas do csv por filename

    for group in grouped:  #percorre os grupos de anotação por filename.: filename_1(anotação_1,anotação_2,...,anotação_n), ..., filename_n(...)
        tf_example = create_tf_example(group, path, label_map)

        if tf_example is None:
            continue

        writer.write(tf_example.SerializeToString())

    writer.close()
    print('Successfully created the TFRecords: {}'.format(OUTPUT_PATH))
