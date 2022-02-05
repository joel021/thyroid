import large_image
import numpy as np
from PIL import Image


def not_content_RGB(p):  # Tome RGB como três eixos coordenados.
    """
  Se a média dos valores RGB estão próximos de 1, então provavelmente são imagens
  em branco.
  Os pixels estão entre 0 e 1.
  """
    return (p[0] - 1) ** 2 + (p[1] - 1) ** 2 + (p[2] - 1) ** 2 <= 0.2 or (p[0]) ** 2 + (p[1]) ** 2 + (
    p[2]) ** 2 <= 0.2 or p[3]


def not_content_RGBA(p):  # Tome RGB como três eixos coordenados.
    """
  Se a média dos valores RGB estão próximos de 1, então provavelmente são imagens
  em branco.
  Os pixels estão entre 0 e 1.
  """
    return (p[0] - 1) ** 2 + (p[1] - 1) ** 2 + (p[2] - 1) ** 2 <= 0.2 or (p[0]) ** 2 + (p[1]) ** 2 + (
    p[2]) ** 2 <= 0.2 or p[3] < 0.9


def extract_by_iterator(file, to_path, type="RGBA", w=512.0, h=512.0):
    i = 0
    s = 0
    ts = large_image.getTileSource(file)

    for interator in ts.tileIterator(
            tile_size=dict(width=w, height=h)):


        im_tile = np.array(interator['tile'])
        tile_mean_rgb = np.mean(im_tile[:, :, :4], axis=(0, 1)) / 255.

        if not not_content_RGB(tile_mean_rgb):
            print(tile_mean_rgb)
            im = Image.fromarray(interator['tile'], type)
            im.save(to_path + "/tile-" + str(i) + ".png")

            if s == 100:
                break

            s = s + 1

        i = i + 1


PATH_FILE_SCANNER = "/media/joel/New Volume/work/TireoideWork/0224-3.svs"
TO_PATH = "/media/joel/New Volume/work/TireoideWork/tiles-0224-3/"
