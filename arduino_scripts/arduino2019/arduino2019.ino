/* Codice per l'Arduino dentro il SUBOTTO */

#include <TM1637Display.h>
#include <Ethernet.h>
#include <utility/w5100.h>

#define DEBUG 1
#define DELAY_ETH_TIME 1000 //milliseconds

#define BRIGHTNESS 7
#define ERROR_TIMEOUT 3*1000

// pin delle fotocellule
#define BLUE_PHOTO_GOAL 37 // gol normale
#define BLUE_PHOTO_SUPERGOAL 39 // supergoal
#define RED_PHOTO_GOAL 41
#define RED_PHOTO_SUPERGOAL 43

// pin dei display
#define CLK_R 50
#define DIO_R 51
#define CLK_B 52
#define DIO_B 53

// pulsanti
#define BLUE_BUTTON_ADD 16
#define BLUE_BUTTON_REMOVE 15
#define RED_BUTTON_ADD 14
#define RED_BUTTON_REMOVE 17
#define reset 8


byte mac[] = { 90, 162, 218, 13, 78, 107};
IPAddress local_ip(10, 0, 0, 2);
// ip del server da interrogare
IPAddress server_ip(10, 0, 0, 1);
int porta = 2204;


EthernetClient client;
unsigned long int tempo = 0;
int tentativi = 0; // tentativi effettuati ad accedere al server

char C = 0;
int z = 10;
int counterrossi = 9999;
int counterblu = 9999; // rischio di overflow

long int last_contact = 0;
long int last_connection_retry = 0;
int loop_num = 0;
char wait = 0;

TM1637Display disp_blu(CLK_B, DIO_B);
TM1637Display disp_rosso(CLK_R, DIO_R);



void receive_data() {
  byte data[4];
  if (!client.connected()) return;
  if (client.available() >= 4) {
    int i;
    for (i = 0; i < 4; i++) {
      data[i] = client.read();
    }
    counterrossi=data[0]*256+data[1];
    counterblu = data[2]*256+data[3];
    last_contact = millis();
  }
}


void Send(uint8_t data) {
  client.write(data);
  #if DEBUG
    Serial.print("benone! invio riuscito: ");
    Serial.println(data);
  #endif
}



void SMS() {
  Send(wait);
}

/*void zero(){
  counterblu=0;
  counterrossi=0;
  }*/

void setup() {

  Serial.begin(9600);

  Serial.println("Inizio programma");
  /*
    Start dell'ethernet
    In produzione, usare begin(mac, ip, dns, gateway, subnet);
    gli indirizzi sono tutti array di 4 byte.
  */
  /*
  Ethernet.begin(mac, local_ip, server_ip, server_ip);
  Serial.println("a");
  if (0) {
    if (DEBUG)
      Serial.println("non connesso!");
  } else
    Serial.println("connesso");
    Serial.println(Ethernet.localIP());

  W5100.setRetransmissionTime(300);
  W5100.setRetransmissionCount(1);
  delay(1000);
  */

  disp_blu.setBrightness(BRIGHTNESS);
  disp_rosso.setBrightness(BRIGHTNESS);

  // All segments on
  //disp_blu.setSegments(data);
  //disp_rosso.setSegments(data);


  // inizializzo i pin dei pulsanti
  pinMode(BLUE_BUTTON_ADD,INPUT_PULLUP);  //blu +
  pinMode(BLUE_BUTTON_REMOVE,INPUT_PULLUP);  //blu -
  pinMode(RED_BUTTON_ADD,INPUT_PULLUP);  //rosso +
  pinMode(RED_BUTTON_REMOVE,INPUT_PULLUP);  //rosso -
  pinMode(reset,INPUT);

  // inizializzo le fotocellule in ingresso, grazie ai lock-in saranno digitali
  pinMode(BLUE_PHOTO_GOAL, INPUT_PULLUP);
  pinMode(BLUE_PHOTO_SUPERGOAL, INPUT_PULLUP);
  pinMode(RED_PHOTO_GOAL, INPUT_PULLUP);
  pinMode(RED_PHOTO_SUPERGOAL, INPUT_PULLUP);

  /*
  client.connect(server_ip, porta);
  receive_data();
  last_contact = millis();
  last_connection_retry = millis();
  */

}



void loop() {
  loop_num++;
  /*
  // Controllo della connessione
  Ethernet.maintain();
  if (((!client.connected()) || (millis() - last_contact >= ERROR_TIMEOUT))
      && (millis() - last_connection_retry >= DELAY_ETH_TIME)) {
    Serial.println(client.connected());
    Serial.println(millis());
    Serial.println(last_contact);
    Serial.println(last_connection_retry);
    counterrossi = 10000;
    counterblu = 10000;
    int res;
    client.stop();
    res = client.connect(server_ip, porta);
    if (DEBUG) {
      Serial.print("connessione persa, riprovo; errore: ");
      Serial.println(res);
    }
    last_contact = millis();
    last_connection_retry = millis();
  }
  receive_data();
  */


  //tutto il necessario per il debug
  if (DEBUG) {
    Serial.print(digitalRead(BLUE_PHOTO_GOAL));Serial.print("  ");
    Serial.print(digitalRead(BLUE_PHOTO_SUPERGOAL));Serial.print("  ");
    Serial.print(digitalRead(RED_PHOTO_GOAL));Serial.print("  ");
    Serial.print(digitalRead(RED_PHOTO_SUPERGOAL));Serial.print("  ");
    Serial.print(digitalRead(BLUE_BUTTON_ADD));Serial.print("  ");
    Serial.print(digitalRead(BLUE_BUTTON_REMOVE));Serial.print("  ");
    Serial.print(digitalRead(RED_BUTTON_ADD));Serial.print("  ");
    Serial.print(digitalRead(RED_BUTTON_REMOVE));Serial.print("  ");
    Serial.println(digitalRead(reset));
  }

  //controllo tutti i possibili input, prima le fotocusu e poi i bottoni
  if (digitalRead(BLUE_PHOTO_GOAL)) {
    if (!wait) {
      wait=1;
    }
    if (DEBUG)
      C++;
  }
  else if (digitalRead(BLUE_PHOTO_SUPERGOAL)) {
    if (!wait) {
      wait=2;
    }
    if (DEBUG)
      C++;
  } else if (digitalRead(RED_PHOTO_GOAL)) {
    if(!wait) {
      wait=3;
    }
    if (DEBUG)
      C++;
  } else if(digitalRead(RED_PHOTO_SUPERGOAL)) {
    if(!wait) {
      wait=4;
    }
    if (DEBUG)
      C++;
  } else if (digitalRead(BLUE_BUTTON_ADD)) {
    if (!wait) {
      wait=5;
    }
    if (DEBUG)
      C++;
  } else if (digitalRead(BLUE_BUTTON_REMOVE)) {
    if (!wait) {
      wait=6;
    }
    if (DEBUG)
      C++;
  } else if(digitalRead(RED_BUTTON_ADD)) {
    if(!wait){
      wait=7;
    }
    if (DEBUG)
      C++;
  } else if(digitalRead(RED_BUTTON_REMOVE)) {
    if(!wait){
      wait=8;
    }
    if (DEBUG)
      C++;
  }
  else if(wait) {
    // invio il risultato
    //SMS();
    wait=0;
  }

  counterblu=10;
  counterrossi=15;

  disp_blu.showNumberDec(counterblu, false);
  disp_rosso.showNumberDec(counterrossi, false);


}
