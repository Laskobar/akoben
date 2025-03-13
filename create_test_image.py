from PIL import Image, ImageDraw

# Créer une image vide (blanc)
width, height = 800, 600
img = Image.new('RGB', (width, height), color='white')
draw = ImageDraw.Draw(img)

# Dessiner des éléments de base pour simuler un graphique de trading
# Axes
draw.line([(50, 50), (50, 550)], fill='black', width=2)  # Axe vertical
draw.line([(50, 550), (750, 550)], fill='black', width=2)  # Axe horizontal

# Ligne simulant un prix
points = [(50, 300)]
for i in range(1, 70):
    x = 50 + i * 10
    y = 300 + (50 * (i % 5) - 100) - i*0.5
    points.append((x, y))

draw.line(points, fill='blue', width=2)

# Quelques bougies japonaises
# Bullish candle
draw.rectangle([(600, 200), (620, 300)], outline='green', fill='white', width=2)
draw.line([(610, 180), (610, 200)], fill='green', width=2)  # Mèche haute
draw.line([(610, 300), (610, 320)], fill='green', width=2)  # Mèche basse

# Bearish candle
draw.rectangle([(650, 220), (670, 320)], outline='red', fill='red', width=2)
draw.line([(660, 200), (660, 220)], fill='red', width=2)  # Mèche haute
draw.line([(660, 320), (660, 340)], fill='red', width=2)  # Mèche basse

# Doji candle
draw.rectangle([(700, 250), (720, 255)], outline='black', fill='white', width=2)
draw.line([(710, 230), (710, 250)], fill='black', width=2)  # Mèche haute
draw.line([(710, 255), (710, 275)], fill='black', width=2)  # Mèche basse

# Ajouter des lignes horizontales pour support et résistance (sans utiliser l'argument dash)
# Pour simuler une ligne pointillée, nous dessinons plusieurs segments courts
for x in range(50, 750, 10):
    draw.line([(x, 400), (x+5, 400)], fill='green', width=1)  # Support
    draw.line([(x, 200), (x+5, 200)], fill='red', width=1)    # Résistance

# Sauvegarder l'image
img.save('data/images/demo_chart.png')
print("Image créée avec succès: data/images/demo_chart.png")