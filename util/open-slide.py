from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
import tensorflow as tf
import numpy as np
from PIL import Image


def extract_cell_group(r, file, model_file):
    model = tf.keras.models.load_model(model_file)
    slide = open_slide(file)
    tiles = DeepZoomGenerator(slide,
                              tile_size=r,  # multiplos de 254
                              overlap=10,
                              limit_bounds=False)
    level = 19
    x_tiles, y_tiles = tiles.level_tiles[level]
    # tiles.get_tile_coordinates(level=20,address=)
    print(x_tiles)
    print(y_tiles)

    for x in range(x_tiles):
        for y in range(y_tiles):
            image = tiles.get_tile(level, (x, y))
            # tile_mean_rgb = np.mean(tile[:, :, :4], axis=(0, 1)) / 255.

            image_array = tf.keras.preprocessing.image.img_to_array(image)
            predict = model.predict(image_array)
            tf.reshape(image_array, (3,3))
            if predict[0][0] > 0.6:
                print(1)
            else:
                print(0)
