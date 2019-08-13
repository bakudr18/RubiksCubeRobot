# RubiksCubeRobot

## Demo
[![](https://img.youtube.com/vi/XAhuqio9FTo/hqdefault.jpg)](https://www.youtube.com/watch?v=XAhuqio9FTo&feature=youtu.be "YouTube Link")
## Introduction
Rubik's Cube Robot can solve the rubik's cube around 90 seconds including detecting and solving. This project is made by 86duino, Maixduino, OV2640 camera, RS-1270 servo motors and ws2812 led strip. The mechanisms refer to [OTVINTA](http://www.rcr3d.com/intro.html) and all of them are 3d printable. The solving algorithm was implemented by [Muodov](https://github.com/muodov/kociemba). He also made a great cube solving machine [Meccano Rubik's Shrine](http://blog.zok.pw/hacking/2016/08/12/meccano-rubiks-shrine/).

You can find more detail [here](http://www.86duino.com/?p=19296&lang=TW) in Chinese.

## Installation
Follow [86duino](http://www.86duino.com/?page_id=2844) and [Maixpy](https://maixpy.sipeed.com/en/) website to set the environment. Upload the main.ino and colorclassification.py into 86Duino and Maixduino respectively.

## Limits
* OV2640 camera's maximum exposure time is 120190us. That's why we added the led strip.
* It's important to fix the lighting environment when detecting colors, so we added the cover on top of the camera. However, we should still avoid direct illumination of the lens.
* Color classification algorithm classifies color white first because white and black are in different dimension of color space than others. Therefore, rubik's cube must have the white color.
