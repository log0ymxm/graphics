import zlib
import struct
import array
import random
import colorsys

def output_chunk(out, chunk_type, data):
    out.write(struct.pack("!I", len(data)))
    out.write(chunk_type)
    out.write(data)
    checksum = zlib.crc32(data, zlib.crc32(chunk_type))
    out.write(struct.pack("!I", checksum))
    #out.write(struct.pack("!I", 0xFFFFFFFF & checksum))

def get_data(width, height, rgb_func):
    fw = float(width)
    fh = float(height)
    compressor = zlib.compressobj()
    data = array.array("B")
    for y in range(height):
        data.append(0)
        fy = float(y)
        for x in range(width):
            fx = float(x)
            data.extend([min(255, max(0, int(v * 255))) for v in rgb_func(fx / fw, fy / fh)])
    compressed = compressor.compress(data.tostring())
    flushed = compressor.flush()
    return compressed + flushed

def write_png(filename, width, height, rgba_func):
    out = open(filename, "wb")
    out.write(array.array('B', [137, 80, 78, 71, 13, 10, 26, 10])) # PNG File Signature
    color_type = 6 if len(list(rgba_func(0,0))) == 4 else 2
    output_chunk(out, "IHDR", struct.pack("!2I5B", width, height, 8, color_type, 0, 0, 0))
    output_chunk(out, "IDAT", get_data(width, height, rgba_func))
    output_chunk(out, "IEND", "")
    out.close()

def linear_gradient(start_value, stop_value, start_offset=0.0, stop_offset=1.0):
    return lambda offset: (start_value + ((offset - start_offset) / (stop_offset - start_offset) * (stop_value - start_value))) / 255.0

def LINEAR_Y(x, y):
    return y

def LINEAR_X(x, y):
    return x

def RADIAL(center_x, center_y):
    return lambda x, y: (x - center_x) ** 2 + (y - center_y) ** 2

def NO_NOISE(r, g, b, a=None):
    if a == None:
        return r, g, b
    else:
        return r, g, b, a

def GAUSSIAN(sigma):
    def add_noise(r, g, b, a=None):
        d = random.gauss(0, sigma)
        if a == None:
            return r + d, g + d, b + d
        else:
            return r + d, g + d, b + d, a
    return add_noise

def HSV(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return 255 * r, 255 * g, 255 * b

def gradient(value_func, noise_func, DATA):
    def gradient_function(x, y):
        initial_offset = 0.0
        v = value_func(x, y)
        for offset, start, end in DATA:
            if v < offset:
                r = linear_gradient(start[0], end[0], initial_offset, offset)(v)
                g = linear_gradient(start[1], end[1], initial_offset, offset)(v)
                b = linear_gradient(start[2], end[2], initial_offset, offset)(v)
                if len(start) == 4:
                    a = linear_gradient(start[3], end[3], initial_offset, offset)(v)
                    return noise_func(r, g, b, a)
                else:
                    return noise_func(r, g, b)
                    
            initial_offset = offset
        return noise_func(end[0] / 255.0, end[1] / 255.0, end[2] / 255.0)
    return gradient_function
