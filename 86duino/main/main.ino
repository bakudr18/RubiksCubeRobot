#include <Servo86.h>
#include <FastLED.h> 
#include <string.h>
#include <stdio.h>

/*
 ported form 
 https://github.com/muodov/kociemba
 */
extern "C"{
  #include "search.h"
}

#define LED_PIN     5 // useless
#define NUM_LEDS    18
#define BRIGHTNESS  200
#define LIGHTOFF    0
#define LED_TYPE    WS2812
#define COLOR_ORDER GRB
CRGB leds[NUM_LEDS];
CRGBPalette16 currentPalette;
TBlendType    currentBlending;


enum { UT = 0, US = 1, RT = 2, RS = 3, LT, LS, DT, DS}; // T : turn, S : slide

Servo myservo[8];

const int DELAY_TIME = 200;
const int CLAMP_UPPER_BOUND = 2100; // rotate 90 degree
const int CLAMP_LOWER_BOUND = 1100; // initial angle 0 degree
const int SLIDE_UPPER_BOUND = 2100;
const int UD_SLIDE_LOWER_BOUND = 965;
const int RL_SLIDE_LOWER_BOUND = 760;
const int UPPER = 0;
const int LOWER = 1;
const int CURR = 2;

int bound[8][3];  // upper bound, lower bound, and current position (us) of each pin

void turning(char *s);
void turningFace(int pin1, int pin2);
void turningCube(int tpin1, int tpin2);
void fixedCube(int latch1, int latch2, bool lock);
void showCube();
void servoRun(int pin, int pos, int delay_time);
void doubleRun(int pin1, int pos1, int pin2, int pos2, int delay_time);

void setup() {
  // turn on the LED
  delay(3000);
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS).setCorrection( TypicalLEDStrip );
  FastLED.setBrightness(  BRIGHTNESS );
  
  currentPalette = RainbowColors_p;
  currentBlending = LINEARBLEND;

  SetupBlackAndWhiteStripedPalette();
  FillLEDsFromPaletteColors(1);
  FastLED.show();
  delay(500);
  // initialize bound tables
  int i;
  for(i = 0; i < 8; i += 2){
    bound[i][UPPER] = CLAMP_UPPER_BOUND;
    bound[i][LOWER] = CLAMP_LOWER_BOUND;
    bound[i + 1][UPPER] = SLIDE_UPPER_BOUND;
  }
  bound[US][LOWER] = bound[DS][LOWER] = UD_SLIDE_LOWER_BOUND;
  bound[RS][LOWER] = bound[LS][LOWER] = RL_SLIDE_LOWER_BOUND;
  for(i = 0; i < 8; i++)
    bound[i][CURR] = bound[i][LOWER];

  // attach the servoes 
  myservo[UT].attach(21);
  myservo[US].attach(22);
  myservo[RT].attach(23);
  myservo[RS].attach(24);
  myservo[LT].attach(25);
  myservo[LS].attach(26);
  myservo[DT].attach(27);
  myservo[DS].attach(28);

  // adjust the mid offset of servo
  myservo[UT].setOffset(-55);
  myservo[RT].setOffset(-50);
  myservo[RS].setOffset(-60);
  myservo[LS].setOffset(40);
  
  // reset to released position
  myservo[DS].setPosition(1600);
  myservo[US].setPosition(1600);
  myservo[RS].setPosition(1600);
  myservo[LS].setPosition(1600);
  servoMultiRun(myservo[DS], myservo[US], myservo[RS], myservo[LS]);
  delay(DELAY_TIME);

  // move clamps to 0 degree
  myservo[DT].setPosition(bound[DT][LOWER]);
  myservo[UT].setPosition(bound[UT][LOWER]);
  myservo[RT].setPosition(bound[RT][LOWER]);
  myservo[LT].setPosition(bound[LT][LOWER]);
  servoMultiRun(myservo[DT], myservo[UT], myservo[RT], myservo[LT]);
  delay(DELAY_TIME);

  // move cube to center position
  myservo[DS].setPosition(bound[DS][LOWER]);
  myservo[US].setPosition(bound[US][LOWER]);
  myservo[RS].setPosition(bound[RS][LOWER]);
  myservo[LS].setPosition(bound[LS][LOWER]);
  servoMultiRun(myservo[DS], myservo[US], myservo[RS], myservo[LS]);
  delay(DELAY_TIME);
  
  Serial.begin(9600);
  Serial1.begin(9600);
}

void loop() {
  char facelets[55];
  
  // wait for finding cube center and setting camera gain
  if(waitUntilFoundCenter() == 0){
    releaseCube();
    while(1);
  }

  // detect 6 faces
  showCube();

  // turn off the led
  FastLED.setBrightness(LIGHTOFF);
  FastLED.show();
  
  // wait until color classification finish
  while(Serial1.available() == 0);
  if(readFacelets(facelets) == 54){
    // sloving by Kociemba's Algorithm
    char *sol = solution(facelets,24,1000,0,"cache");
    if (sol == NULL) {
      Serial.println("Unsolvable cube!");
      releaseCube();
      while(1);
    }

    // adjust the solution because of turning cube F and B
    adjustSolFace(sol);
    Serial.println(sol);

    // split the string to turning cube
    char *pch;
    pch = strtok (sol," ");
    while (pch != NULL)
    {
      Serial.println(pch);
      turning(pch);
      pch = strtok (NULL, " ");
    }
    free(sol);
  }

  // release cube
  releaseCube();
  while(1);
}
