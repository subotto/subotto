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
        for ( int   i = 0 ; i < 4 ; ++i)
        {
                lc.setDigit(0,i+display_number,number%10, false);
                number /= 10; 
                if (number == 0 ) return ;
        }
}

void loop()
{
  if (Serial.available()>0)
  {
    int input = Serial.parseInt();
    if (input == COM_RESET) {
      setup();
    } else if (input >=16384)
    {
      refreshDisplay(input);
     // Serial.println(input);
    }
  Serial.println(input);
  }
}
