import glob
import openpyxl as px

wb = px.Workbook()
ws = wb.active
ws.title = 'result'

filepaths = glob.glob('data/**/*.jpg', recursive=True)

# Header
ws.append(['#', 'ファイル', 'Serial', 'テキスト', '見つかった文字', '画像'])
for i, w in enumerate([5, 50, 5, 30, 15, 30]):
  col = px.utils.get_column_letter(i + 1)
  ws.column_dimensions[col].width = w

# body
for r, fp in enumerate(filepaths, 2):
  cols = [r - 1, fp, 999, 'TEXT TEXT TEXT', 'A B C', fp]
  ws.append(cols)
  img = px.drawing.image.Image(cols[5])
  ws.add_image(img, 'F' + str(r))
  ws.row_dimensions[r].height = img.height * 0.75 + 1

wb.save('aaa.xlsx')
