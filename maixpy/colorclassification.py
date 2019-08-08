import sensor, image, time, lcd, math
from machine import UART
from board import board_info
from fpioa_manager import fm


roi = (25, 5, 110, 110)

lcd.init()

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time = 600)

fm.register(board_info.PIN10, fm.fpioa.UART2_TX) # maixduino pin 12
fm.register(board_info.PIN15, fm.fpioa.UART2_RX) # maixduino pin 7
uart = UART(UART.UART2, 9600, 8, None, 1, timeout = 1000, read_buf_len = 4096)

class P_control:
    """
    P control to set exposure time
    """
    def __init__(self, P=0.2):

        self.Kp = P

        self.SetPoint = 0.0

        self.output = 0.0

    def update(self, feedback_value):
        error = self.SetPoint - feedback_value
        self.output = self.Kp * error

    def setKp(self, proportional_gain):
        self.Kp = proportional_gain

def isSquare(r):
    """
    check if the rectangle is square
    """
    SQUARE_THRESHOLD = 5
    right_angle_threshold = 10.0
    cnr = r.corners()
    lines = []
    diag_lines = []
    for i in range(4):
        lines.append(math.sqrt((cnr[i][0] - cnr[(i+1) % 4][0])**2 + (cnr[i][1] - cnr[(i+1) % 4][1])**2))
        diag_lines.append(math.sqrt((cnr[i][0] - cnr[(i+2) % 4][0])**2 + (cnr[i][1] - cnr[(i+2) % 4][1])**2))
    for i in range(4):
        if (abs(lines[i] - lines[(i+1) % 4]) > SQUARE_THRESHOLD):
            return False
        if (lines[i] * lines[(i+1) % 4] < 500):
            return False
        deg = math.degrees(math.acos( (lines[i]**2 + lines[ (i+1) % 4]**2 - diag_lines[i]**2) / (2 * lines[i] * lines[ (i+1) % 4] + 0.0001) ))
        if (abs(90 - deg) > right_angle_threshold):
            return False

    return True

def getEuclidean(point1, point2):
    """
    Euclidean Distance
    """
    dimension = len(point1)
    dist = 0.0
    for i in range(dimension):
        dist += (point1[i] - point2[i]) ** 2
    return math.sqrt(dist)

def findCenter(squares, roi, center_threshold):
    """
    find the center of new roi
    """
    c_orig = (roi[0] + roi[2] / 2, roi[1] + roi[3] / 2)
    min_dist = center_threshold
    min_idx = -1
    for i, r in enumerate(squares):
        c_r = (r.x() + r.w() / 2, r.y() + r.h() / 2)
        dist = int(getEuclidean(c_orig, c_r))
        if dist <= center_threshold and dist <= min_dist:
            min_dist = dist
            min_idx = i
    if min_idx == -1:
        return roi
    else:
        return list(map(int,[roi[0] + (squares[min_idx].x() + squares[min_idx].w() / 2 - c_orig[0]),
                             roi[1] + (squares[min_idx].y() + squares[min_idx].h() / 2 - c_orig[1]),
                             roi[2], roi[3]]))

def clamp_roi(roi):
    """
    find four clamps roi position
    """
    wid = 10
    ht = 10
    x = int(roi[0] + (roi[2] - wid) / 2)
    y = int(roi[1] + (roi[3] - ht) / 2)
    clp_roi = [[roi[0], y, wid, ht],
               [x, roi[1], wid, ht],
               [roi[0] + roi[2] - wid, y, wid, ht],
               [x, roi[1] + roi[3] - ht, wid, ht]]
    for r in clp_roi:
       if r[0] < 0: r[0] = 0
       if r[1] < 0: r[1] = 0
       if r[0] >= sensor.width(): r[0] = sensor.width() - 1
       if r[1] >= sensor.height(): r[1] = sensor.height() - 1
       if r[0] + r[2] > sensor.width(): r[2] = sensor.width() - r[0]
       if r[1] + r[3] > sensor.height(): r[3] = sensor.height() - r[1]
    print(clp_roi)
    return clp_roi

def split_roi(roi):
    # split square to Jiugongge
    sub_roi = []
    wid = int(roi[2] / 3)
    leng = int(roi[3] / 3)
    for i in range(3):
        for j in range(3):
            lst = []
            lst.append(roi[0] + wid * i)
            lst.append(roi[1] + leng * j)
            lst.append(wid)
            lst.append(leng)
            sub_roi.append(lst)
    return sub_roi

def center_rect(roi, percentage):
    # reduce side length to target percentage
    wid = roi[2] * percentage / 100
    ht = roi[3] * percentage / 100
    x = roi[0] + (roi[2] - wid) / 2
    y = roi[1] + (roi[3] - ht) / 2
    '''
    if x < 0: x = 0
    if y < 0: y = 0
    if x + wid > sensor.width(): wid = sensor.width() - int(x) - 1
    if y + ht > sensor.height(): ht = sensor.height() - int(y) - 1
    '''
    return list(map(int,[x ,y, wid, ht]))

def __RGB_to_Hue(var_R, var_G, var_B, var_min, var_max):
    if var_max == var_min:
        return 0.0
    elif var_max == var_R:
        return (60.0 * ((var_G - var_B) / (var_max - var_min)) + 360) % 360.0
    elif var_max == var_G:
        return 60.0 * ((var_B - var_R) / (var_max - var_min)) + 120.0
    elif var_max == var_B:
        return 60.0 * ((var_R - var_G) / (var_max - var_min)) + 240.0

def RGB_to_HSV(rgb_r, rgb_g, rgb_b):
   """
   Converts from RGB to HSV.
   H values are in degrees and are 0 to 360.
   S values are a percentage, 0.0 to 1.0.
   V values are a percentage, 0.0 to 1.0.
   """
   var_R = rgb_r
   var_G = rgb_g
   var_B = rgb_b

   var_max = max(var_R, var_G, var_B)
   var_min = min(var_R, var_G, var_B)

   var_H = __RGB_to_Hue(var_R, var_G, var_B, var_min, var_max)

   if var_max == 0:
       var_S = 0
   else:
       var_S = 1.0 - (var_min / var_max)

   var_V = var_max / 255

   return (var_H, var_S, var_V)

def dot(a, b):
    return [sum([a[j][i]*b[i] for i in range(len(b))]) for j in range(len(b))]

def XYZ_to_RGB(xyz_x, xyz_y, xyz_z):
    """
    XYZ to RGB conversion.
    """
    temp_X = xyz_x
    temp_Y = xyz_y
    temp_Z = xyz_z

    rgb_matrix = [[3.24071, -1.53726, -0.498571],\
                  [-0.969258, 1.87599, 0.0415557],\
                  [0.0556352, -0.203996, 1.05707]]
    temp_XYZ = [xyz_x, xyz_y, xyz_z]
    # rgb_matrix dot temp_XYZ
    rgb_r, rgb_g, rgb_b = dot(rgb_matrix, temp_XYZ)

    # v
    linear_channels = dict(r=rgb_r, g=rgb_g, b=rgb_b)
    # V
    nonlinear_channels = {}
    for channel in ['r', 'g', 'b']:
        v = linear_channels[channel]
        if v <= 0.0031308:
            nonlinear_channels[channel] = v * 12.92
        else:
            nonlinear_channels[channel] = 1.055 * math.pow(v, 1 / 2.4) - 0.055

    return (nonlinear_channels['r'] * 255, nonlinear_channels['g'] * 255, nonlinear_channels['b'] * 255)

def Lab_to_XYZ(lab_l, lab_a, lab_b):
    """
    Convert from Lab to XYZ
    """
    CIE_E = 216.0 / 24389.0
    illum = (0.95047, 1.00000, 1.08883) #By default Observer = 2A, Illuminant= D65.

    xyz_y = (lab_l + 16.0) / 116.0
    xyz_x = lab_a / 500.0 + xyz_y
    xyz_z = xyz_y - lab_b / 200.0

    if math.pow(xyz_y, 3) > CIE_E:
        xyz_y = math.pow(xyz_y, 3)
    else:
        xyz_y = (xyz_y - 16.0 / 116.0) / 7.787

    if math.pow(xyz_x, 3) > CIE_E:
        xyz_x = math.pow(xyz_x, 3)
    else:
        xyz_x = (xyz_x - 16.0 / 116.0) / 7.787

    if math.pow(xyz_z, 3) > CIE_E:
        xyz_z = math.pow(xyz_z, 3)
    else:
        xyz_z = (xyz_z - 16.0 / 116.0) / 7.787

    xyz_x = (illum[0] * xyz_x)
    xyz_y = (illum[1] * xyz_y)
    xyz_z = (illum[2] * xyz_z)

    return (xyz_x, xyz_y, xyz_z)

def Lab_to_RGB(lab_l, lab_a, lab_b):
    return XYZ_to_RGB(*Lab_to_XYZ(lab_l, lab_a, lab_b))

def lab_mode(img, roi):
    stc = img.get_statistics(roi = roi)
    lab_l_mode, lab_a_mode, lab_b_mode = stc.l_mode(), stc.a_mode(), stc.b_mode()
    print("lab_mode.append([", lab_l_mode,"," ,lab_a_mode,",", lab_b_mode,"])")
    return [lab_l_mode, lab_a_mode, lab_b_mode]

def hsv_mode(img, roi):
    stc = img.get_statistics(roi = roi)
    hsv_h_mode,  hsv_s_mode, hsv_v_mode = RGB_to_HSV(*Lab_to_RGB(stc.l_mode(), stc.a_mode(), stc.b_mode()))
    print("hsv_mode.append([", hsv_h_mode,"," ,hsv_s_mode,",", hsv_v_mode,"])")
    return [hsv_h_mode, hsv_s_mode, hsv_v_mode]

def lab_median(img, roi):
    stc = img.get_statistics(roi = roi)
    lab_l_median, lab_a_median, lab_b_median = stc.l_median(), stc.a_median(), stc.b_median()
    return [lab_l_median, lab_a_median, lab_b_median]

def saturation_sort(hsv):
    """
    sort by saturation to classify white color
    """
    s_index = sorted(range(len(hsv)), key = lambda k : hsv[k][1])
    #print(s_index)
    return s_index[0:9]

def hue_sort(hsv):
    """
    sorting red, orange, yellow, green and blue
    note that the difference between red and blue is obvious so it can be easily divided.
    """
    red_blue_divide = 280
    h = [x[0] if x[0] < red_blue_divide else (x[0] - 360) for x in hsv]
    h = sorted(range(len(h)), key = lambda k : h[k])
    return h

def permutations(iterable, r = None):
    """
    ported from standard library itertools
    https://docs.python.org/2/library/itertools.html#itertools.permutations
    """
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return
    indices = list(range(n))
    cycles = list(range(n, n-r, -1))
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return

def check_facelets(facelets):
    """
    check the facelets have different center, edge and corner square
    """
    center = ['U', 'R', 'F', 'D', 'L', 'B']
    edge = ['UF', 'UR', 'UB', 'UL', 'DF', 'DR', 'DB', 'DL', 'FR', 'RB', 'BL', 'LF']
    corner = ['UFL', 'ULB', 'UBR', 'URF', 'DFL', 'DLB', 'DBR', 'DRF']

    edgestr = [facelets[1] + facelets[46], facelets[3] + facelets[37], facelets[5] + facelets[10], facelets[7] + facelets[19],\
               facelets[41] + facelets[21], facelets[23] + facelets[12], facelets[14] + facelets[48], facelets[50] + facelets[39],\
               facelets[25] + facelets[28], facelets[32] + facelets[16], facelets[30] + facelets[43], facelets[34] + facelets[52]]

    cornerstr = [facelets[6] + facelets[18] + facelets[38], facelets[8] + facelets[9] + facelets[20],\
                 facelets[0] + facelets[36] + facelets[47], facelets[2] + facelets[11] + facelets[45],\
                 facelets[24] + facelets[27] + facelets[44], facelets[15] + facelets[26] + facelets[29],\
                 facelets[33] + facelets[42] + facelets[53], facelets[17] + facelets[35] + facelets[51]]
    for i,c in enumerate(center):
        #assert facelets[4 + i*9] == c , "Center Error:" + c
        if facelets[4 + i*9] != c: print("Center Error:" + c)

    for i,square in enumerate(edgestr):
        for c in edge:
            pmt = [''.join(p) for p in permutations(c)]
            if square in pmt:
                edge.remove(c)
                break
        #assert len(edge) == len(edgestr) - (i + 1) , "Edge Error:" + square
        if len(edge) != len(edgestr) - (i + 1): print("Edge Error:" + square)

    for i,square in enumerate(cornerstr):
        for c in corner:
            pmt = [''.join(p) for p in permutations(c)]
            if square in pmt:
                corner.remove(c)
                break
        #assert len(corner) == len(cornerstr) - (i + 1) , "Corner Error:" + square
        if len(corner) != len(cornerstr) - (i + 1): print("Corner Error:" + square)

def to_matrix(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def rotate_matrix(matrix, cw = True):
    if cw:
        return list(zip(*matrix[::-1]))
    else:
        return list(zip(*matrix))[::-1]

def color_classify(hsv):
    """
    classify color and adjust the face order to URFDLB
            |************|                                                  |************|
            |*U1**U2**U3*|                                                  |*00**01**02*|
            |************|                                                  |************|
            |*U4**U5**U6*|                                                  |*03**04**05*|
            |************|                                                  |************|
            |*U7**U8**U9*|                                                  |*06**07**08*|
            |************|                                                  |************|
************|************|************|************             ************|************|************|************
*L1**L2**L3*|*F1**F2**F3*|*R1**R2**R3*|*B1**B2**B3*             *36**37**38*|*18**19**20*|*09**10**11*|*45**46**47*
************|************|************|************             ************|************|************|************
*L4**L5**L6*|*F4**F5**F6*|*R4**R5**R6*|*B4**B5**B6*             *39**40**41*|*21**22**23*|*12**13**14*|*48**49**50*
************|************|************|************             ************|************|************|************
*L7**L8**L9*|*F7**F8**F9*|*R7**R8**R9*|*B7**B8**B9*             *42**43**44*|*24**25**26*|*15**16**17*|*51**52**53*
************|************|************|************             ************|************|************|************
            |************|                                                  |************|
            |*D1**D2**D3*|                                                  |*27**28**29*|
            |************|                                                  |************|
            |*D4**D5**D6*|                                                  |*30**31**32*|
            |************|                                                  |************|
            |*D7**D8**D9*|                                                  |*33**34**35*|
            |************|                                                  |************|
    """
    labels = []
    for i in range(len(hsv)):
        labels.append(-1)

    # check white color
    wh_index = saturation_sort(hsv)
    for wh_i in wh_index:
        labels[wh_i] = 0
    print(wh_index)
    # check other colors
    hue_index = hue_sort(hsv)
    for i in wh_index:
        if i in hue_index:
            hue_index.remove(i)
    index = 0
    for i,hi in enumerate(hue_index):
        if i % 9 == 0:
            index += 1
        labels[hi] = index

    # adjust face to URFDLB
    # LDRUFB(camera scanning order) to URFDLB
    labels =[labels[27:36], labels[18:27], labels[36:45], labels[9:18], labels[0:9], labels[45:54]]
    # adjust matrix direction caused by camera
    l = []
    for i in range(6):
        ma = to_matrix(labels[i],3)
        if i == 1:
            ma = rotate_matrix(ma)
        elif i == 3 or i == 5:
            ma = rotate_matrix(ma)
            ma = rotate_matrix(ma)
        elif i == 4:
            ma = rotate_matrix(ma, False)

        ma = [e for t in ma for e in t]
        l.extend(ma)
    labels = l
    print(labels)
    # turn 0~5 to URFDLB
    face = ['U', 'R', 'F', 'D', 'L', 'B']
    face_dict = {}
    for i in range(6):
        face_dict[labels[4 + i*9]] = face[i]

    facelets = []
    for item in labels:
        if item in face_dict:
            facelets.append(face_dict[item])
        else:
            print("white color error:", item)
            return 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBUBBBB' # return an unsolvable cube
    facelets = ''.join(facelets)

    #check_facelets
    check_facelets(facelets)
    return facelets

def exposure_compensation():
    """
    use P control to set the exposure time according to the clamps brightness
    """
    P = 2000

    pid = P_control(P)

    pid.SetPoint = 40
    END = 50
    expo = sensor.get_exposure_us()

    for i in range(1, END):
        img = sensor.snapshot()
        llist = []
        for r in clamp_roi(roi):
            lab = lab_median(img, r)
            img = img.draw_rectangle(r)
            llist.append(lab[0])

        l_mean = int(sum(llist) / len(llist))
        print("l_mean = ", l_mean)
        img = img.draw_rectangle(roi)

        if abs(l_mean - pid.SetPoint) <= 1:
            sensor.set_saturation(2)
            return

        pid.update(l_mean)
        output = pid.output
        expo += int(output)
        if expo < 10000:
            sensor.set_auto_gain(0)
            expo = sensor.get_exposure_us()
            sensor.set_auto_exposure(0, expo)
            P = P / 2
            continue
        if sensor.get_exposure_us() >= 120190:
            sensor.set_saturation(2)
            return  # max exposure time

        sensor.set_auto_exposure(0, expo)
        sensor.skip_frames(n = 60)
        print("exp time",sensor.get_exposure_us())

def findCubeCenter():
    """
    find the cube roi position
    """
    global roi
    sensor.set_auto_whitebal(False)
    sensor.set_contrast(2)

    cnt = 1
    LAB_THRESHOLD = ((0, 60, -40, 50, -40, 10), # blue
                     (0, 40, -50, 40, -60, 30), # yellow orange red white
                     (0, 50, -40, 15, -25, 70))
                     #(0, 70, -25, 15, -60, 30)) # green

    CENTER_THRESHOLD = roi[2] / 3 / 2
    gain = 0
    while(True):

        if cnt > 12:
            sensor.set_auto_gain(gain)

        img = sensor.snapshot()

        if cnt % 60 == 0:
            cnt = 1
            gain += 10

        if (int(cnt / 24)) % 2 == 1:
            lab_threshold = LAB_THRESHOLD[ int(cnt / 12) - 2]
            img = img.binary([lab_threshold])
            img = img.dilate(2)
            img = img.erode(2)

        lcd.display(img)

        center_roi = list(map(int,[roi[0] + roi[2] / 2 - CENTER_THRESHOLD * 2, roi[1] + roi[3] / 2 - CENTER_THRESHOLD * 2,
                                   CENTER_THRESHOLD * 4, CENTER_THRESHOLD * 4]))
        squares = []
        for r in img.find_rects(roi = center_roi, threshold = 500):
            if(isSquare(r)):
                squares.append(r)
                img = img.draw_rectangle(r.rect())
                for p in r.corners(): img = img.draw_circle(p[0], p[1], 5, color = (0, 255, 0))
                lcd.display(img)
                #time.sleep_ms(5000)
        if not squares:
            cnt += 1
            print(cnt)
        else:
            roi = findCenter(squares, roi, CENTER_THRESHOLD * math.sqrt(2))
            center_roi = list(map(int,[roi[0] + roi[2] / 2 - CENTER_THRESHOLD * 2, roi[1] + roi[3] / 2 - CENTER_THRESHOLD * 2,
                                       CENTER_THRESHOLD * 4, CENTER_THRESHOLD * 4]))
            img = img.draw_rectangle(center_roi)
            img = img.draw_rectangle(roi)

            lcd.display(img)

            sensor.reset()
            sensor.set_pixformat(sensor.RGB565)
            sensor.set_framesize(sensor.QQVGA)

            sensor.set_auto_whitebal(False)
            sensor.skip_frames(time = 60)
            gain = sensor.get_gain_db()
            sensor.set_auto_gain(0, gain)
            sensor.skip_frames(time = 60)
            sensor.set_auto_exposure(0, 80000)

            sensor.skip_frames(time = 60)
            return 1



def main():
    while(True):
        img = sensor.snapshot()
        img = img.draw_rectangle(roi)
        read_data = uart.read()
        if read_data is not None:
            read_str = str(read_data, "utf-8")
            print(read_str)
            if read_str == "true":
                found = findCubeCenter()
                exposure_compensation()
                if found:
                    uart.write("true")
                else:
                    print("find center fail")
                    uart.write("false")
                break

    print("expose time = ", sensor.get_exposure_us())
    hsv_list = []
    scale = 3
    midp = list(map(int,(roi[0] + roi[2] / 2 - 4 * 3, roi[1] + roi[3] / 2 - 5 * 3)))
    cnt = 0

    while(True):
        read_data = uart.read()
        if read_data is not None:   # check if face is ready to snapsoht
            img = sensor.snapshot()
            read_str = str(read_data, "utf-8")
            if read_str == "true":
                sub_roi = split_roi(roi)
                for i, r in enumerate(sub_roi): # save color space data
                    r = center_rect(r, 50)
                    hsv = hsv_mode(img, r)
                    hsv_list.append(hsv)

                cnt += 1
                img = img.draw_rectangle(roi)
                img.draw_string(midp[0], midp[1], str(cnt), color = 255, scale = scale)
                tmp = lcd.display(img)

            uart.write(read_str)
        if len(hsv_list) == 54:
            break

    facelets = color_classify(hsv_list)
    print(facelets)
    uart.write(facelets)

main()
