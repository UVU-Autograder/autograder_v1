from PIL import Image

filename = 'bears_copy.jpg'
filepath = f"./{filename}"

balloon_filename = 'balloon.png'  # use the real transparent PNG
balloon_filepath = f"./{balloon_filename}"

file_out = 'bears3.jpg'
file_out_path = f"./{file_out}"

# Load the original bear image, and get its size and color mode.
orig_image = Image.open(filepath)
width, height = orig_image.size
mode = orig_image.mode

# Load the balloon image, keeping its alpha (transparency) channel.
balloon_image = Image.open(balloon_filepath).convert('RGBA')
balloon_width, balloon_height = 130, 210
balloon_image = balloon_image.resize((balloon_width, balloon_height))

# Load pixels from both images.
orig_pixel_map = orig_image.load()
balloon_pixel_map = balloon_image.load()

# Create a new image matching the original image's color mode and size.
new_image = Image.new(mode, (width, height))
new_pixel_map = new_image.load()

# Choose where the top-left corner of the balloon will go.
start_x, start_y = 100, 50

# Copy every pixel from the original bear image into the new image.
for x in range(width):
    for y in range(height):
        new_pixel_map[x, y] = orig_pixel_map[x, y]

# Overlay the balloon: only copy pixels where alpha > 0,
# i.e. pixels that are actually part of the balloon, not background.
for bx in range(balloon_width):
    for by in range(balloon_height):
        r, g, b, a = balloon_pixel_map[bx, by]
        if a > 0:
            new_pixel_map[start_x + bx, start_y + by] = (r, g, b)

new_image.save(file_out_path)