/* Codice per l'Arduino dentro il SUBOTTO */

#include <TM1637Display.h>

#define DEBUG 1

// pin delle fotocellule
#define BLUE_PHOTO_GOAL 37 // gol normale
#define BLUE_PHOTO_SUPERGOAL 39 // supergoal
#define RED_PHOTO_GOAL 41
#define RED_PHOTO_SUPERGOAL 43

// pin dei display
#define CLK_RED 50
#define DIO_RED 51
#define CLK_BLUE 52
#define DIO_BLUE 53

#define BRIGHTNESS 7

// pulsanti
#define BLUE_BUTTON_ADD 16
#define BLUE_BUTTON_REMOVE 15
#define RED_BUTTON_ADD 14
#define RED_BUTTON_REMOVE 17
#define RESET 8

#define numpins 9



TM1637Display disp_blu(CLK_BLUE, DIO_BLUE);
TM1637Display disp_rosso(CLK_RED, DIO_RED);


class Controller {
    int pins[numpins] = {BLUE_PHOTO_GOAL, BLUE_PHOTO_SUPERGOAL, RED_PHOTO_GOAL, RED_PHOTO_SUPERGOAL, BLUE_BUTTON_ADD, BLUE_BUTTON_REMOVE, RED_BUTTON_ADD, RED_BUTTON_REMOVE, RESET};
    bool state[numpins] = {false,false,false,false,false,false,false,false,false};
    int points_red = 9999;
    int points_blue = 9999;

    void act(int pin) {
        switch(pin) {
            case BLUE_PHOTO_GOAL: points_blue++; break;
            case BLUE_PHOTO_SUPERGOAL: points_blue++; break;
            case RED_PHOTO_GOAL: points_red++; break;
            case RED_PHOTO_SUPERGOAL: points_red++; break;
            case BLUE_BUTTON_ADD: points_blue++; break;
            case BLUE_BUTTON_REMOVE: points_blue--; break;
            case RED_BUTTON_ADD: points_red++; break;
            case RED_BUTTON_REMOVE: points_red--; break;
            default: break;
        }
    }

  public:
    void update() {
        for (int i=0;i<numpins;i++) {
            bool res = digitalRead(pins[i]);
            if (res && !state[i]) act(pins[i]);
            state[i] = res;
        }
    }

    void show() {
        disp_blu.showNumberDec(points_blue, false);
        disp_rosso.showNumberDec(points_red, false);
    }

    void print_state() {
        for (int i=0;i<numpins;i++) {
            Serial.print(state[i]); Serial.print(" ");
        }
        Serial.println();
    }
};



Controller controller;

void setup() {

  Serial.begin(9600);

  Serial.println("Inizio programma");


  disp_blu.setBrightness(BRIGHTNESS);
  disp_rosso.setBrightness(BRIGHTNESS);

  // All segments on
  //disp_blu.setSegments(data);
  //disp_rosso.setSegments(data);


  // inizializzo i pin dei pulsanti
  pinMode(BLUE_BUTTON_ADD,INPUT_PULLUP);
  pinMode(BLUE_BUTTON_REMOVE,INPUT_PULLUP);
  pinMode(RED_BUTTON_ADD,INPUT_PULLUP);
  pinMode(RED_BUTTON_REMOVE,INPUT_PULLUP);
  pinMode(RESET,INPUT);

  // inizializzo le fotocellule in ingresso, grazie ai lock-in saranno digitali
  pinMode(BLUE_PHOTO_GOAL, INPUT_PULLUP);
  pinMode(BLUE_PHOTO_SUPERGOAL, INPUT_PULLUP);
  pinMode(RED_PHOTO_GOAL, INPUT_PULLUP);
  pinMode(RED_PHOTO_SUPERGOAL, INPUT_PULLUP);

}



void loop() {
  //tutto il necessario per il debug
  if (DEBUG) {
    controller.print_state();
  }

  controller.update();

  controller.show();

}
