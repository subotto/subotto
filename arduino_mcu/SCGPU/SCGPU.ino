#include "opcodes.h"
#include "LedControl.h"


// Porte di I/O su Arduino

#define BLUE_NORMAL_PIN 5
#define BLUE_SUPER_PIN 4
#define RED_NORMAL_PIN 6
#define RED_SUPER_PIN 7

#define BLUE_ADD_PIN 9
#define BLUE_UNDO_PIN 12
#define RED_ADD_PIN 11
#define RED_UNDO_PIN 10

#define SOFT_RESET_PIN A3

// Interfacce seriali 

#define SPI_CLK A1		// Clock
#define SPI_MOSI A0		// Master Out Slave In 
#define SPI_MISO 100	// Master In Slave Out - per i led non ci serve questa porta

#define SPI_DISPLAY_LOAD A2	 // Load per il display


// Settaggi

#define GOAL_DELAY 3000
#define PUSH_DELAY 1000
#define DELAY 10


// Costanti del programma

#define TEST_MODE 0
#define SLAVE_MODE 1
#define MASTER_MODE 2

#define SUB_NONE -1

int mode;	// l'attuale modalità di lavoro
unsigned long last_goal;	// il millis dell'ultimo goal
unsigned long last_push;	// il millis dell'ultima pressione di pulsante

int blue_normal_enable = 1;
int blue_super_enable = 1;
int red_normal_enable = 1;
int red_super_enable = 1;

unsigned long blue_score = 0;
unsigned long red_score = 0;

LedControl lc=LedControl(SPI_MOSI, SPI_CLK,SPI_DISPLAY_LOAD,1);

void writeInteger(int number, int display_number)
//	Scrivi l'intero numero su display (0 o 1)
//	Gli zeri iniziali vengono buttati via
//	Le cifre 0 (per display 0) e 4 (per display 1) sono le più significative
{
        display_number *= 4;
        int i;
        for ( i = 0 ; i < 4 ; ++i)
        {
                if (number == 0 && i!=0) {
                  lc.setChar(0,i+display_number,' ',false);
                }
                else {
                  lc.setDigit(0,i+display_number,number%10, false);
                }
                number /= 10; 
        }
}

void setup()
{
  pinMode(BLUE_NORMAL_PIN,INPUT);
  pinMode(BLUE_SUPER_PIN,INPUT);
  pinMode(RED_NORMAL_PIN,INPUT);
  pinMode(RED_SUPER_PIN,INPUT);
  
  pinMode(BLUE_ADD_PIN,INPUT_PULLUP);
  pinMode(BLUE_UNDO_PIN,INPUT_PULLUP);
  pinMode(RED_ADD_PIN,INPUT_PULLUP);
  pinMode(RED_UNDO_PIN,INPUT_PULLUP);
  
  pinMode(SOFT_RESET_PIN,INPUT_PULLUP);
  
  pinMode(13,OUTPUT);		// led per debug
  digitalWrite(13,LOW);
  
  blue_normal_enable = 1;
  blue_super_enable = 1;
  red_normal_enable = 1;
  red_super_enable = 1;
  
  blue_score = 0;
  red_score = 0;

  Serial.begin(115200);
  
  mode = MASTER_MODE;
//  last_goal = millis();
//  last_push = millis();
  last_goal = 0;
  last_push = 0;
  
  // Inizializzazione del display
  /*
   The MAX72XX is in power-saving mode on startup,
   we have to do a wakeup call
   */
  lc.shutdown(0,false);
  /* Set the brightness to a medium values */
  lc.setIntensity(0,8);
  /* and clear the display */
  lc.clearDisplay(0);
  writeInteger(0,0);
  writeInteger(0,1);
  
  Serial.println(SUB_READY);
}

void loop()
{
  int input = -1;
  if (Serial.available()>0)
  {
    input = Serial.parseInt();
    
    int consumed = 1;
    switch (input) {
      case COM_ECHO_TEST:
        Serial.println(SUB_ECHO_REPLY);
        break;
      case COM_SET_SLAVE_MODE:
        mode = SLAVE_MODE;
        Serial.println(SUB_SLAVE_MODE);
        break;
      case COM_SET_TEST_MODE:
        mode = TEST_MODE;
        Serial.println(SUB_TEST_MODE);
        break;
      case COM_SET_MASTER_MODE:
        mode = MASTER_MODE;
        blue_score = 0;
        red_score = 0;
        write_points();
        Serial.println(SUB_MASTER_MODE);
        break;
      case COM_RESET:
        setup();
        break;
      default:
        consumed = 0;
    }
    if (input >= 16384)
    {
      refreshDisplay(input);
      Serial.println(input);
    }
    if (consumed) return;
  }

  switch (mode) {
  	case TEST_MODE:
  	  test_main(input);
  	  break;
  	case SLAVE_MODE:
  	  slave_main(input);
  	  break;
  	case MASTER_MODE:
          master_mode(input);
          break;
    }
  
  delay(DELAY);
  
}

void test_main(int input)
{
  int result = -1;
  
  // Se mi è stato chiesto di leggere un sensore rispondo
  if (input == COM_BLUE_NORMAL_TEST)
    result = digitalRead(BLUE_NORMAL_PIN);
  else if (input == COM_BLUE_SUPER_TEST)
    result = digitalRead(BLUE_SUPER_PIN);
  else if (input == COM_RED_NORMAL_TEST)
    result = digitalRead(RED_NORMAL_PIN);
  else if (input == COM_RED_SUPER_TEST)
    result = digitalRead(RED_SUPER_PIN);

  if (result != -1) {
    //Serial.println(result);
    if (result == 0) {
      Serial.println(SUB_TEST_OPEN);
    } else {
      Serial.println(SUB_TEST_CLOSE);
    }
  }
  
}

void slave_main(int input)
{
  switch (input)
  {
    case COM_ENABLE_RED_NORMAL:
      red_normal_enable = 1;
      Serial.println(SUB_RED_NORMAL_ENABLED);
      break;
    case COM_ENABLE_RED_SUPER:
      red_super_enable = 1;
      Serial.println(SUB_RED_SUPER_ENABLED);
      break;
    case COM_ENABLE_BLUE_NORMAL:
      blue_normal_enable = 1;
      Serial.println(SUB_BLUE_NORMAL_ENABLED);
      break;
    case COM_ENABLE_BLUE_SUPER:
      blue_super_enable = 1;
      Serial.println(SUB_BLUE_SUPER_ENABLED);
      break;
    case COM_DISABLE_RED_NORMAL:
      red_normal_enable = 0;
      Serial.println(SUB_RED_NORMAL_DISABLED);
      break;
    case COM_DISABLE_RED_SUPER:
      red_super_enable = 0;
      Serial.println(SUB_RED_SUPER_DISABLED);
      break;
    case COM_DISABLE_BLUE_NORMAL:
      blue_normal_enable = 0;
      Serial.println(SUB_BLUE_NORMAL_DISABLED);
      break;
    case COM_DISABLE_BLUE_SUPER:
      blue_super_enable = 0;
      Serial.println(SUB_BLUE_SUPER_DISABLED);
      break;    
  }
  
  int result = scan_input();
  if (result != SUB_NONE)
  {
  	Serial.println(result);
  }
  
}

void master_mode(int input)
{
  int result = scan_input();
  if (!digitalRead(SOFT_RESET_PIN))
  {
    blue_score = 0;
    red_score = 0;
    update_points(); 
  }
  
  switch (result)
  {
  	// ++red
  	case SUB_PHOTO_BLUE_NORMAL:
  	case SUB_PHOTO_BLUE_SUPER:
  	case SUB_BUTTON_RED_GOAL:
  	  ++red_score;
  	  update_points();
  	  break;
  	// --blue
  	case SUB_BUTTON_BLUE_UNDO:
  	    --blue_score;
  	  update_points();
  	  break;
  	// ++blue
  	case SUB_PHOTO_RED_NORMAL:
  	case SUB_PHOTO_RED_SUPER:
  	case SUB_BUTTON_BLUE_GOAL:
  	  ++blue_score;
  	  update_points();
  	  break;
  	// --red
  	case SUB_BUTTON_RED_UNDO:
  	    --red_score;
  	  update_points();
  	  break;
  }

}



int scan_input ()
{
  // Scansione delle fotocellule
  if (millis() > last_goal + GOAL_DELAY)
  {
     if (blue_normal_enable && digitalRead(BLUE_NORMAL_PIN))
     {
       last_goal = millis();
       return SUB_PHOTO_BLUE_NORMAL;
     }
     if (blue_super_enable && digitalRead(BLUE_SUPER_PIN))
     {
       last_goal = millis();
       return SUB_PHOTO_BLUE_SUPER;
     }
     if (red_normal_enable && digitalRead(RED_NORMAL_PIN))
     {
       last_goal = millis();
       return SUB_PHOTO_RED_NORMAL;
     }
     if (red_super_enable && digitalRead(RED_SUPER_PIN))
     {
       last_goal = millis();
       return SUB_PHOTO_RED_SUPER;
     }
  }


  // Scansione dei pulsanti
  if (millis() > last_push + PUSH_DELAY)
//  if (0 == 1)		// non sono ancora collegati
  {
    if (!digitalRead(BLUE_ADD_PIN))
    {
      last_push = millis();
      return SUB_BUTTON_BLUE_GOAL;
    }
    if (!digitalRead(BLUE_UNDO_PIN))
    {
      last_push = millis();
      return SUB_BUTTON_BLUE_UNDO; 
    }
    if (!digitalRead(RED_ADD_PIN))
    {
      last_push = millis();
      return SUB_BUTTON_RED_GOAL;
    }
    if (!digitalRead(RED_UNDO_PIN))
    {
      last_push = millis();
      return SUB_BUTTON_RED_UNDO;
    }
  }
  return SUB_NONE;
}

void update_points()
{
	if (blue_score<0)
	{
		blue_score = 0;
	}
	if (red_score<0)
	{
		red_score = 0;
	}
/*	if ((blue_score >= 6 && blue_score > red_score +1) || (red_score >= 6 && red_score > blue_score + 1))
		{
			blue_score = 0;
			red_score = 0;
		}
*/
	write_points();
}

void write_points()
{
  writeInteger(blue_score,0); 
  writeInteger(red_score,1);
}


// Aggiorna i display con l'input che arriva dal computer)
void refreshDisplay(int input)
{
  input -= 16384;
  writeInteger ( input % 8192 , input/8192);
}
