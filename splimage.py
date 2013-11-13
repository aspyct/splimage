import Image
from operator import add
from operator import div

vertical = True
horizontal = not vertical

class SplitCountError(ValueError): pass

# TODO Should elect a separator color after the first pass
# and stick to it.
# The decision should be base on:
#    occurrence frequency
#    closeness to other pixels
# 
# We can also maybe adjust the threshold based on the selected color

def slice_steps(filename, image_count=None):
    # TODO Automatically adjust threshold based on image_count
    image = Image.open(filename)

    print repr(cut_image(image, vertical, 25, image_count))
    return

    # bisect the optimal threshold
    threshold = 128
    next_step = threshold / 2

    while 1:
        print "Threshold is:", threshold
        try:
            parts = cut_image(image, vertical, threshold, image_count)
            print "Number of parts:", len(parts)
            
            if len(parts) == image_count:
                return parts
            else: # too few, raise threshold
                threshold = threshold + next_step
        except SplitCountError: # too many, lower threshold
            threshold = threshold - next_step

        if next_step == 0: # damn, we've covered every threshold
            raise ValueError("Cannot find adequate threshold")

        next_step = next_step / 2


def cut_image(image, direction, threshold, max_split):
    parts = _cut_image(image, direction, threshold, max_split)

    assert len(parts) > 0

    if len(parts) == 1 or len(parts) == max_split:
        return parts
    else:
        split_parts = []
        max_subsplits = max_split - len(parts) + 1 # + 1 because we don't count this one
        assert max_subsplits > 1

        for part in parts:
            # Take each part, and split it into smaller chunks
            for subpart in cut_image(part, not direction, threshold, max_subsplits):
                 split_parts.append(subpart)

        return split_parts


# And now for the beefy part
def _cut_image(image, direction, threshold, max_split):
    # print "Cutting", image
    previous_color = None
    
    separators = []
    row = 0
    
    # find separators
    for line in lines(image, direction):
        #print "On to line", row
        if is_separator(line, threshold):
            separators.append(row)

        row += 1

    last_row = row - 1

    if not separators:
        # nothing to split, we're done here
        return [image]

    # reduce separators to images
    # 1. make all possible subimages
    span_start = 0
    spans = []
    
    for span_end in separators:
        if span_end > span_start: # if there's at least one pixel between each
            spans.append((span_start, span_end))

        span_start = span_end + 1
    
    print "Groups:", spans
    if not spans or len(spans) > max_split:
        raise SplitCountError("Too many splits")
    
    # 2. make actual image crops
    images = []
    for span in spans:
        images.append(sub_image(image, direction, span[0], span[1]))

    return images


def sub_image(image, direction, span_start, span_end):
    if direction == vertical:
        x = 0
        width = image.size[0]
        y = span_start
        height = span_end
    else:
        x = span_start
        width = span_end
        y = 0
        height = image.size[1]

    # print "Cropping to", (x, y, width, height)
    return image.crop((x, y, width, height))


def is_separator(line, threshold):
    # FIXME Should take in account that the separator should always have the same color
    count = 0
    total = (0, 0, 0)
    pixels = []
    
    # compute the average color of the line
    for pixel in line:
        total = map(add, total, pixel)

        count += 1
        pixels.append(pixel)

    # TODO keep the average as the "likely separator color" and refine later
    average = tuple(map(div, total, (count, count, count)))

    # now check that each pixel is within the average + threshold
    for pixel in pixels:
        if not colors_match(average, pixel, threshold):
            return False
    else:
        print "Average is:", repr(average)
        return True


def colors_match(color_a, color_b, threshold):
    # FIXME There must be a better way...
    return abs(color_a[0] - color_b[0]) <= threshold and \
           abs(color_a[1] - color_b[1]) <= threshold and \
           abs(color_a[2] - color_b[2]) <= threshold

def lines(image, direction):
    if direction == vertical:
        end = image.size[1]
    else:
        end = image.size[0]

    for i in range(0, end):
        yield line(image, direction, i)


def line(image, direction, row):
    pixmap = image.load()

    if direction == vertical:
        # we want a horizontal line of pixels
        line = horizontal_line(image, row)
    else:
        # otherwise, give a vertical line of pixels
        line = vertical_line(image, row)

    for pixel in line:
        yield pixmap[pixel]


def horizontal_line(image, row):
    for i in range(0, image.size[0]):
        yield (i, row)

def vertical_line(image, column):
    for i in range(0, image.size[1]):
        yield (column, i)


def main():
    import sys
    slice_steps("sample.jpg", 3)


if __name__ == "__main__":
    main()

