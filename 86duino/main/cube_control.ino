void chr_replace(char *orig, char *rep, char *with){
  char *s;
  char *pr, *pw;
  if(strlen(rep) != strlen(with))
    return;
  
  for(s = orig; *s != '\0'; s++)
    for(pr = rep, pw = with; *pr != '\0'; pr++, pw++)
      if(*s == *pr){
        *s = *pw;
        break;
      }
}

void adjustSolFace(char *sol){
  char *s;
  for(s = sol; *s != '\0'; s++){
    if(*s == 'F')
      chr_replace(s + 1, "FBUD", "UDBF");
    else if(*s == 'B')
      chr_replace(s + 1, "BFUD", "UDFB");
  }
}

void turning(char *s){
  int i;
  if(strcmp(s, "U") == 0)
    turningFace(UT, US); 
  else if(strcmp(s, "U\'") == 0)
    turningFace(US, UT);
  else if(strcmp(s, "U2") == 0)
    for(i = 0; i < 2; i++)
      turningFace(UT, US);
  else if(strcmp(s, "D") == 0)
    turningFace(DT, DS);
  else if(strcmp(s, "D\'") == 0)
    turningFace(DS, DT);
  else if(strcmp(s, "D2") == 0)
    for(i = 0; i < 2; i++)
      turningFace(DT, DS);
  else if(strcmp(s, "R") == 0)
    turningFace(RT, RS);
  else if(strcmp(s, "R\'") == 0)
    turningFace(RS, RT);
  else if(strcmp(s, "R2") == 0)
    for(i = 0; i < 2; i++)
      turningFace(RT, RS);
  else if(strcmp(s, "L") == 0)
    turningFace(LT, LS);
  else if(strcmp(s, "L\'") == 0)
    turningFace(LS, LT);
  else if(strcmp(s, "L2") == 0)
    for(i = 0; i < 2; i++)
      turningFace(LT, LS);
  else if(strcmp(s, "X") == 0)
    turningCube(LT, RT);
  else if(strcmp(s, "X\'") == 0)
    turningCube(RT, LT);
  else if(strcmp(s, "X2") == 0)
    for(i = 0; i < 2; i++)
      turningCube(LT, RT);
  else if(strcmp(s, "Y") == 0)
    turningCube(DT, UT);
  else if(strcmp(s, "Y\'") == 0)
    turningCube(UT, DT);
  else if(strcmp(s, "Y2") == 0)
    for(i = 0; i < 2; i++)
      turningCube(UT, DT);
  else if(strcmp(s, "F") == 0){
    turning("X");
    turning("U");
  }
  else if(strcmp(s, "F\'") == 0){
    turning("X");
    turning("U\'");
  }
  else if(strcmp(s, "F2") == 0){
    turning("X");
    for(i = 0; i < 2; i++)
      turning("U");
  }
   else if(strcmp(s, "B") == 0){
    turning("X\'");
    turning("U");
  }
  else if(strcmp(s, "B\'") == 0){
    turning("X\'");
    turning("U\'");
  }
  else if(strcmp(s, "B2") == 0){
    turning("X\'");
    for(i = 0; i < 2; i++)
      turning("U");
  }
}

void turningFace(int pin1, int pin2){
  if( pin1 >= 8 || pin1 < 0 || pin2 >= 8 || pin2 < 0)
    return;
  int latch1, latch2;
  if( pin1 == US || pin1 == UT || pin1 == DS || pin1 == DT){
    latch1 = RT;
    latch2 = LT;
  }
  else{
    latch1 = UT;
    latch2 = DT;
  }
  fixedCube(latch1, latch2, true);
  servoRun(pin1, bound[pin1][UPPER], DELAY_TIME);
  servoRun(pin2, bound[pin2][UPPER], DELAY_TIME);
  servoRun(pin1, bound[pin1][LOWER], DELAY_TIME);
  servoRun(pin2, bound[pin2][LOWER], DELAY_TIME);
  fixedCube(latch1, latch2, false);
}

void turningCube(int tpin1, int tpin2){
  if( tpin1 >= 8 || tpin1 < 0 || tpin2 >= 8 || tpin2 < 0 || tpin1 % 2 != 0 || tpin2 % 2 != 0) // check turning pin
    return;
  int tlatch1, tlatch2, slatch1, slatch2, spin1, spin2;
  if(tpin1 == UT || tpin1 == DT){
    tlatch1 = RT;
    tlatch2 = LT;
  }
  else{
    tlatch1 = UT;
    tlatch2 = DT;
  }
  spin1 = tpin1 + 1;
  spin2 = tpin2 + 1;
  slatch1 = tlatch1 + 1;
  slatch2 = tlatch2 + 1;
  
  fixedCube(tlatch1, tlatch2, true);
  servoRun(spin1, bound[spin1][UPPER], DELAY_TIME);
  servoRun(tpin1, bound[tpin1][UPPER], DELAY_TIME);
  servoRun(spin1, bound[spin1][LOWER], DELAY_TIME);
  fixedCube(tlatch1, tlatch2, false);
  doubleRun(slatch1, bound[slatch1][UPPER], slatch2, bound[slatch2][UPPER], DELAY_TIME);

  doubleRun(tpin1, bound[tpin1][LOWER], tpin2, bound[tpin2][UPPER], DELAY_TIME);

  doubleRun(slatch1, bound[slatch1][LOWER], slatch2, bound[slatch2][LOWER], DELAY_TIME);
  fixedCube(tlatch1, tlatch2, true);
  servoRun(spin2, bound[spin2][UPPER], DELAY_TIME);
  servoRun(tpin2, bound[tpin2][LOWER], DELAY_TIME);
  servoRun(spin2, bound[spin2][LOWER], DELAY_TIME);
  fixedCube(tlatch1, tlatch2, false);
}

void fixedCube(int latch1, int latch2, bool lock){
  // fix the cube by the rest of clamps to avoid sliding
  if(lock == true)
    doubleRun(latch1, bound[latch1][LOWER] + 50, latch2, bound[latch2][LOWER] + 50, 30);
  else
    doubleRun(latch1, bound[latch1][LOWER], latch2, bound[latch2][LOWER], 30);
}

void showFace(int tpin1, int tpin2){
  // turn the clamps to 90 degree to show the face of cube
  if( tpin1 >= 8 || tpin1 < 0 || tpin2 >= 8 || tpin2 < 0 || tpin1 % 2 != 0 || tpin2 % 2 != 0) // check turning pin
    return;
  int tlatch1, tlatch2, slatch1, slatch2, spin1, spin2;
  if(tpin1 == UT || tpin1 == DT){
    tlatch1 = RT;
    tlatch2 = LT;
  }
  else{
    tlatch1 = UT;
    tlatch2 = DT;
  }
  spin1 = tpin1 + 1;
  spin2 = tpin2 + 1;
  slatch1 = tlatch1 + 1;
  slatch2 = tlatch2 + 1;
  
  fixedCube(tlatch1, tlatch2, true);
  doubleRun(spin1, bound[spin1][UPPER], spin2, bound[spin2][UPPER], DELAY_TIME);
  doubleRun(tpin1, bound[tpin1][UPPER], tpin2, bound[tpin2][UPPER], DELAY_TIME);
  doubleRun(spin1, bound[spin1][LOWER], spin2, bound[spin2][LOWER], DELAY_TIME);
  fixedCube(tlatch1, tlatch2, false);
  doubleRun(slatch1, bound[slatch1][UPPER], slatch2, bound[slatch2][UPPER], DELAY_TIME);
  waitUntilSnapshot();  // snapshot
  doubleRun(slatch1, bound[slatch1][LOWER], slatch2, bound[slatch2][LOWER], DELAY_TIME);

}

void showCube(){
  // show 6 faces of cube
  int i;
  for(i = 0; i < 4; i++){
    showFace(UT, DT);
    if( i == 3)
      break;
    fixedCube(RT, LT, true);
    servoRun(US, bound[US][UPPER], DELAY_TIME);
    servoRun(UT, bound[UT][LOWER], DELAY_TIME);
    servoRun(US, bound[US][LOWER], DELAY_TIME);
    fixedCube(RT, LT, false);
    doubleRun(RS, bound[RS][UPPER], LS, bound[LS][UPPER], DELAY_TIME);
    doubleRun(UT, bound[UT][UPPER], DT, bound[DT][LOWER], DELAY_TIME);
    doubleRun(RS, bound[RS][LOWER], LS, bound[LS][LOWER], DELAY_TIME);
  }
  fixedCube(RT, LT, true);
  doubleRun(US, bound[US][UPPER], DS, bound[DS][UPPER], DELAY_TIME);
  doubleRun(UT, bound[UT][LOWER], DT, bound[DT][LOWER], DELAY_TIME);
  doubleRun(US, bound[US][LOWER], DS, bound[DS][LOWER], DELAY_TIME);
  fixedCube(RT, LT, false);

  for(i = 0; i < 4; i++){
    if( i == 1 || i == 3)
      showFace(RT, LT);
    if( i == 3)
      break;
    fixedCube(UT, DT, true);
    doubleRun(RS, bound[RS][UPPER], LS, bound[LS][UPPER], DELAY_TIME);
    doubleRun(RT, bound[RT][LOWER], LT, bound[LT][UPPER], DELAY_TIME);
    doubleRun(RS, bound[RS][LOWER], LS, bound[LS][LOWER], DELAY_TIME);
    fixedCube(UT, DT, false);
    doubleRun(US, bound[US][UPPER], DS, bound[DS][UPPER], DELAY_TIME);
    doubleRun(RT, bound[RT][UPPER], LT, bound[LT][LOWER], DELAY_TIME);
    doubleRun(US, bound[US][LOWER], DS, bound[DS][LOWER], DELAY_TIME);
  }
  fixedCube(UT, DT, true);
  doubleRun(RS, bound[RS][UPPER], LS, bound[LS][UPPER], DELAY_TIME);
  doubleRun(RT, bound[RT][LOWER], LT, bound[LT][LOWER], DELAY_TIME);
  doubleRun(RS, bound[RS][LOWER], LS, bound[LS][LOWER], DELAY_TIME);
  fixedCube(UT, DT, false);
}

void releaseCube(){
  myservo[DS].setPosition(1600);
  myservo[US].setPosition(1600);
  myservo[RS].setPosition(1600);
  myservo[LS].setPosition(1600);
  servoMultiRun(myservo[DS], myservo[US], myservo[RS], myservo[LS]);
  delay(DELAY_TIME);
}

void servoRun(int pin, int pos, int delay_time){
  if(bound[pin][CURR] == pos)
    return;
  myservo[pin].setPosition(pos);
  myservo[pin].run();
  delay(delay_time);
  bound[pin][CURR] = pos; 
}

void doubleRun(int pin1, int pos1, int pin2, int pos2, int delay_time){
  if(bound[pin1][CURR] == pos1 && bound[pin2][CURR] == pos2)
    return;
  myservo[pin1].setPosition(pos1);
  myservo[pin2].setPosition(pos2);
  servoMultiRun(myservo[pin1], myservo[pin2]);
  delay(delay_time);
  bound[pin1][CURR] = pos1;
  bound[pin2][CURR] = pos2;
}
