void waitUntilSnapshot(){
  Serial1.write("true");
  while(1){
    if(Serial1.available() > 0 && Serial1.find("true"))
      return;
  }
}

int waitUntilFoundCenter(){
  Serial1.write("true");
  while(1){
    if(Serial1.available() > 0){
      if(Serial1.find("true"))
        return 1;
      else if(Serial1.find("false"))
        return 0;
    }
  }
}

int readFacelets(char *facelets){  
  int c, i;
  i = 0;
  while(Serial1.available() > 0){
    if(i < 54){
        c = Serial1.read();
        if(c == -1){
          Serial1.println("error: missing facelets");
          return -1;
        }
        facelets[i] = c;
        facelets[++i] = '\0';
    }
  }
  return i;
}
