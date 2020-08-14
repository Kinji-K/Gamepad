#include "Keyboard.h"

const int sw_pin = 9;
const int Button[7] ={2,3,4,5,6,7,8};
const char key_assign[7] = {'z','x','a','s',KEY_ESC,'q','w',};
const int Toggle = 10;
const int x_pin = A0;
const int y_pin = A1;
const float move_max = 10;

int sw = 0;
int x_pos = 0;
int y_pos = 0;
int BTN[7] = {0};
int Count[7] = {0};
int Count_arrow[2] = {0};
int TGL = 0;

// スティックの読み取り値からカウンタ値を返す関数
int count_arrow_memory(float Distance){
  if (Distance > 2){
    return 1;
  } else if (Distance < -2){
    return -1;
  } else {
    return 0;
  }
}

// スティックの読み取り値とカウンタ値から方向キーの入力をする関数
void arrow_input(float Distance, int count, int up, int down){
  if (Distance > 2 && count == 1){
    Keyboard.press(up);
  } else if (Distance < -2 && count == -1) {
    Keyboard.press(down);
  } else if (Distance >= -2 && Distance <=2 && count == 0){
    Keyboard.release(up);
    Keyboard.release(down);
  }
}


void setup() {
  // put your setup code here, to run once:
  pinMode(sw_pin, INPUT_PULLUP);
  for (int i=0; i<7; i++){ 
    pinMode(Button[i], INPUT);
  }
  pinMode(Toggle, INPUT);
  Serial.begin(9600);
  Keyboard.begin();
}

void loop() {
  // put your main code here, to run repeatedly:
  // 各入力の読み取り
  x_pos = analogRead(x_pin);
  y_pos = analogRead(y_pin);
  for (int i=0; i<7; i++){
    BTN[i] = digitalRead(Button[i]);
  }
  TGL = digitalRead(Toggle);

  float xDistance = (float)x_pos / 1023.0f * move_max - 5;
  float yDistance = (float)y_pos / 1023.0f * move_max - 5;

  // トグルがonのときのみキーボード入力をする
  if (TGL == HIGH){

    // ボタンの入力操作
    for (int i=0;i<7;i++){
      // 入力状態がonかつカウンタがonならキーを押下
      if(BTN[i]==HIGH && Count[i]==1){
        Keyboard.press(key_assign[i]);
      // 入力状態がoffかつカウンタがoffならキーを離す
      } else if (BTN[i]==LOW && Count[i]==0){
        Keyboard.release(key_assign[i]);
      }
    }

    // スティックの入力操作
    arrow_input(xDistance, Count_arrow[0],KEY_RIGHT_ARROW, KEY_LEFT_ARROW);
    arrow_input(yDistance, Count_arrow[1],KEY_UP_ARROW, KEY_DOWN_ARROW);
    
  } else {
    Serial.println ("Off");
    Keyboard.releaseAll();
  }
  
    
  // カウンタの更新
  for (int i=0; i<7; i++){
    if (BTN[i]==HIGH){
      Count[i] = 1;
    } else {
      Count[i] = 0;
    }
  }

  Count_arrow[0] = count_arrow_memory(xDistance);
  Count_arrow[1] = count_arrow_memory(yDistance);
  
  delay(20);

}
