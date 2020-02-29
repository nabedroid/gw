#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from gimpfu import *

# layer name : layer color
LAYER_COLORS = {
  'A1' : (0, 255, 0),
  'A2' : (255, 255, 0),
  'A3' : (0, 0, 255),
  'A4' : (255, 0, 0),
  'C1' : (128, 0, 0),
  'C2' : (0, 128, 0),
  'C3' : (0, 0, 128),
  'C4' : (128, 128, 128),
  'D' : (255, 0, 255)
}

# undo group decorator
def undo(func):
  def wrapper(*args, **kwargs):
    args[0].undo_group_start()
    func(*args, **kwargs)
    args[0].undo_group_end()
  return wrapper

@undo
def addLayer(image, drawable):
  w = image.width
  h = image.height
  for dmg in reversed(sorted(LAYER_COLORS.keys())):
    # skip existing layer
    if pdb.gimp_image_get_layer_by_name(image, dmg): continue
    layer = gimp.Layer(image, dmg, w, h, RGB_IMAGE, 100, NORMAL_MODE)
    image.add_layer(layer, 0)
    pdb.gimp_layer_add_alpha(layer)
    pdb.gimp_edit_clear(layer)
  sort_layers(image, drawable)

@undo
def exportPngPsd(image, drawable):

  sort_layers(image, drawable)
  move_correct_layer(image, drawable)

  # save as png/psd
  # get image filepath
  filepath = pdb.gimp_image_get_filename(image)
  # without extension
  filepath = os.path.splitext(filepath)[0]
  # save as png
  # merge layers in memory, after remove the image in memory
  tmpImage = pdb.gimp_image_duplicate(image)
  layer = pdb.gimp_image_merge_visible_layers(tmpImage, CLIP_TO_IMAGE)
  pdb.file_png_save_defaults(tmpImage, layer, filepath + '.png', filepath + '.png')
  pdb.gimp_image_delete(tmpImage)
  # save as psd
  pdb.file_psd_save(image, drawable, filepath + '.psd', filepath + '.psd', 0, 0)

def move_correct_layer(image, drawable):
  for layer in image.layers:
    # skip background
    if not layer.name in LAYER_COLORS: continue
    for k, c in LAYER_COLORS.items():
      # skip own color
      if k == layer.name: continue
      pdb.gimp_image_select_color(image, 0, layer, c)
      bounds = pdb.gimp_selection_bounds(image)
      # exist invalid color bound
      if bounds[0]:
        pdb.gimp_edit_cut(layer)
        toLayer = pdb.gimp_image_get_layer_by_name(image, k)
        fsel = pdb.gimp_edit_paste(toLayer, False)
        pdb.gimp_floating_sel_anchor(fsel)
      pdb.gimp_selection_clear(image)

def sort_layers(image, drawable):
  # background to top
  sortLayers = sorted(image.layers, key=lambda layer: layer.name if layer.name in LAYER_COLORS else "z")

  # reorder layers
  for i, layer in enumerate(sortLayers):
    layer.visible = True
    layer.linked = False
    pdb.gimp_image_reorder_item(image, layer, None, i)

#register old style
register(
  'python_fu_seg030_add_layer',
  'add A1 to C4 layers',
  'add A1 to C4 layers',
  'nabedroid',
  'nabedroid',
  '2020',
  '<Image>/seg030/Add Layer...',
  'RGB*, GRAY*',
  [],
  [],
  addLayer)

register(
  'python_fu_seg030_export',
  'export as png/psd',
  'export as png/psd',
  'nabedroid',
  'nabedroid',
  '2020',
  '<Image>/seg030/export...',
  'RGB*, GRAY*',
  [],
  [],
  exportPngPsd)

main()