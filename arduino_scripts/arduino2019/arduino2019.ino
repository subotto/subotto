/* Codice per l'Arduino dentro il SUBOTTO */

#include <TM1637Display.h>
#include <Ethernet.h>
#include <SPI.h>
#include <utility/w5100.h>

#define DEBUG 1

// times in milliseconds
#define ETH_DELAY_TIME 3000
#define UPDATE_INTERVAL 500
#define ETH_DHCP 60000

#define BRIGHTNESS 7

// pin delle fotocellule
#define BLUE_PHOTO_GOAL 39 // gol normale
#define BLUE_PHOTO_SUPERGOAL 37 // supergoal
#define RED_PHOTO_GOAL 41
#define RED_PHOTO_SUPERGOAL 43

// pin dei display
#define CLK_BLUE 30
#define DIO_BLUE 31
#define CLK_RED 32
#define DIO_RED 33

// pulsanti
#define BLUE_BUTTON_ADD 15
#define BLUE_BUTTON_REMOVE 14
#define RED_BUTTON_ADD 16
#define RED_BUTTON_REMOVE 17

#define numpins 9

byte mac[] = { 90, 162, 218, 13, 78, 107};
// ip del server da interrogare
IPAddress server_ip(192, 168, 251, 167);
int porta = 2204;

long int last_dhcp = 0;


TM1637Display disp_blu(CLK_BLUE, DIO_BLUE);
TM1637Display disp_rosso(CLK_RED, DIO_RED);



class Controller {
    int pins[numpins] = {0,BLUE_PHOTO_GOAL, BLUE_PHOTO_SUPERGOAL, RED_PHOTO_GOAL, RED_PHOTO_SUPERGOAL, BLUE_BUTTON_ADD, BLUE_BUTTON_REMOVE, RED_BUTTON_ADD, RED_BUTTON_REMOVE};
    bool state[numpins] = {false,false,false,false,false,false,false,false,false};

    int points_red = 8888;
    int points_blue = 9999;

    EthernetClient client;

    long int last_contact = 0;
    long int last_connection_retry = 0;

    bool check_connection() {
      if (client.connected()) {
        return true;
      }
      if (millis()-last_connection_retry > ETH_DELAY_TIME) {
        client.stop();
        bool res = client.connect(server_ip, porta);
        last_connection_retry = millis();
        if (DEBUG) {
          Serial.print("connessione persa, riprovo; nuovo stato: ");
          Serial.println(res);
        }
        return res;
      }
      return false;
    }

    void Send(uint8_t data) {
      bool conn = check_connection();
      if (!conn) return;
      client.write(data);
      #if DEBUG
        Serial.print("benone! invio riuscito: ");
        Serial.println(data);
      #endif
    }

  public:
    void init_connection() {
      client.connect(server_ip, porta);
      last_connection_retry = millis();
      Serial.print("init_conn: "); Serial.println(client.connected());
    }

    void update() {
        for (int i=1;i<numpins;i++) {
            bool res = digitalRead(pins[i]);
            if (res && !state[i]) Send(i);
            state[i] = res;
        }
    }

    void receive_data() {
      if (millis() - last_contact < UPDATE_INTERVAL) return;
      bool conn = check_connection();
      if (!conn) return;
      Serial.println("rec_data");
      byte data[4];
      if (client.available() >= 4) {
        int i;
        for (i = 0; i < 4; i++) {
          data[i] = client.read();
        }
        points_red = data[0]*256+data[1];
        points_blue = data[2]*256+data[3];
        last_contact = millis();
      }
    }

    void show() {
        disp_blu.showNumberDec(points_blue, false);
        disp_rosso.showNumberDec(points_red, false);
    }

    void print_state() {
        for (int i=1;i<numpins;i++) {
            Serial.print(state[i]); Serial.print(" ");
        }
        Serial.println();
    }
};



Controller controller;

void setup() {

  Serial.begin(9600);

  Serial.println("Inizio programma");

  // Inizializzazione Ethernet con DHCP
  Ethernet.init(10);
  int dhcp = Ethernet.begin(mac);

  if (DEBUG) {
    if (Ethernet.hardwareStatus() == EthernetNoHardware)
      Serial.println("Ethernet shield was not found.");
    else if (Ethernet.hardwareStatus() == EthernetW5100)
      Serial.println("W5100 Ethernet controller detected.");
    else if (Ethernet.hardwareStatus() == EthernetW5200)
      Serial.println("W5200 Ethernet controller detected.");
    else if (Ethernet.hardwareStatus() == EthernetW5500)
      Serial.println("W5500 Ethernet controller detected.");
  }


  if (!dhcp) {
    Serial.println("non connesso!");
  } else {
    Serial.println("connesso");
    Serial.println(Ethernet.localIP());
  }

  last_dhcp = millis();

  //W5100.setRetransmissionTime(300);
  //W5100.setRetransmissionCount(1);
  //delay(1000);

  disp_blu.setBrightness(BRIGHTNESS);
  disp_rosso.setBrightness(BRIGHTNESS);

  // inizializzo i pin dei pulsanti
  pinMode(BLUE_BUTTON_ADD,INPUT_PULLUP);  //blu +
  pinMode(BLUE_BUTTON_REMOVE,INPUT_PULLUP);  //blu -
  pinMode(RED_BUTTON_ADD,INPUT_PULLUP);  //rosso +
  pinMode(RED_BUTTON_REMOVE,INPUT_PULLUP);  //rosso -
  //pinMode(reset,INPUT);

  // inizializzo le fotocellule in ingresso, grazie ai lock-in saranno digitali
  pinMode(BLUE_PHOTO_GOAL, INPUT_PULLUP);
  pinMode(BLUE_PHOTO_SUPERGOAL, INPUT_PULLUP);
  pinMode(RED_PHOTO_GOAL, INPUT_PULLUP);
  pinMode(RED_PHOTO_SUPERGOAL, INPUT_PULLUP);

  controller.init_connection();

}



void loop() {

  // Controllo del DHCP lease
  if (millis()-last_dhcp > ETH_DHCP) {
    Ethernet.maintain();
    last_dhcp = millis();
  }

  // leggi il punteggio
  controller.receive_data();

  // guarda i sensori e manda eventuali gol al server
  controller.update();

  // stampa lo stato
  if (DEBUG) {
    controller.print_state();
  }


  controller.show();


}
