#include "LedControl.h"
#include "opcodes.h"

// Interfacce seriali 

#define SPI_CLK 11              // Clock
#define SPI_MOSI 12             // Master Out Slave In 
#define SPI_MISO 100    // Master In Slave Out - per i led non ci serve questa porta

#define SPI_DISPLAY_LOAD 10      // Load per il display

LedControl lc=LedControl(SPI_MOSI, SPI_CLK,SPI_DISPLAY_LOAD,1);

void setup()
{
  Serial.begin(115200);
  
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

void refreshDisplay(int input)
{
  input -= 16384;
  writeInteger ( input % 8192 , 1-input/8192);
}

void writeInteger(int number, int display_number)

//      Scrivi l'intero numero su display (0 o 1)
//      Gli zeri iniziali vengono buttati via
//      Le cifre 0 (per display 0) e 4 (per display 1) sono le più significative

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

void loop() {
  while (Serial.available() > 0) {
    int input = Serial.parseInt();
    
    if (Serial.read() == '\n') {
      Serial.println(input);
      if (input == COM_RESET) {
        setup();
      }
      else if (input >=16384) {
        refreshDisplay(input);
       // Serial.println(input);
      }
    }
  }
}

/* Scritte utili:

  lc.setRow(0,3,B01011110);
  lc.setDigit(0,2,0, false);
  lc.setChar(0,1,'A', false);
  lc.setChar(0,0,'L', false);
  
  
  lc.setChar(0,3,' ', false);
  lc.setDigit(0,2,2, false);
  lc.setDigit(0,1,4, false);
  lc.setChar(0,0,'H', false);
*/
