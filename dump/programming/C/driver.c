#include<stdio.h>
#include<stdlib.h>
#include <time.h>
#include <sys/time.h>

#include <fcntl.h>
#include<unistd.h>
#include<error.h>
#include<linux/ppdev.h>
#include<linux/parport.h>
#include <sys/ioctl.h>

/*una stupida funzione per stampare i byte in formato leggibile da un umano*/
void print_byte(unsigned char ch){
	printf("%d%d%d%d%d%d%d%d",(ch&128)/128,(ch&64)/64,(ch&32)/32,(ch&16)/16,(ch&8)/8,(ch&4)/4,(ch&2)/2,
(ch&1)/1);
}

int drive_printer (const char *name) {
    int fd;

    /* Un po'  di settaggi iniziali*/
    fd = open (name, O_RDWR);
    if (fd == -1) {
       perror ("open");
        return 1;
    }

    if (ioctl (fd, PPCLAIM)) {
       perror ("PPCLAIM");
        close (fd);
        return 1;
    }

/* */
unsigned char dat=0;
ioctl(fd , PPWDATA , &dat);

int set=1;
ioctl(fd,PPDATADIR,&set);

/* Set time last goal */
struct timeval last_time;
struct timeval new_time;
gettimeofday(&last_time,NULL);
int irqc;
/* Il tempo minimo tra due goal, in microsecondi*/
int interval = 2000000;
/* Il tempo tra due letture, in microsecondi*/
int read_interval=1000;
int valid_bits = 1+4;

    /* Wait for an interrupt. */
    while (1) {
        fd_set rfds;
        FD_ZERO (&rfds);
        FD_SET (fd, &rfds);
        if (!select (fd + 1, &rfds, NULL, NULL, NULL)){
          /* Caught a signal? */
          continue;
	}
	ioctl (fd, PPCLRIRQ, &irqc);
	/* Controlla che siano passati almeno interval microsecondi dall'ultimo interrupt */
	gettimeofday(&new_time,NULL);
	if ((new_time.tv_sec- last_time.tv_sec)*1000000 + (new_time.tv_usec - last_time.tv_usec) > interval) {
	        unsigned char ch;
/* 		ioctl(fd,PPRSTATUS,&ch);
		printf("Status line: ");
		print_byte(ch);
		printf("\n");*/
/*		while (1){
			ioctl(fd,PPRDATA,&ch);
			if (ch & valid_bits == valid_bits) continue;
		/*	usleep(read_interval);*/
/*		}*/
		ioctl(fd,PPRDATA,&ch);
		if ((~ch)&1) printf("1");
/*		if (!(ch&2)) printf("2");*/
		if ((~ch)&4) printf("3");
/*		if (!(ch&8)) printf("4");*/
		printf("\n");
		fflush(stdout);

		last_time.tv_sec=new_time.tv_sec;
		last_time.tv_usec = new_time.tv_usec;
	}
	/*printf("Interrupt received: %d.%d %d.%d\n",last_time.tv_sec,last_time.tv_usec,new_time.tv_sec,new_time.tv_usec);*/
      }


    /* Okay, finished */
    ioctl (fd, PPRELEASE);
    close(fd);
}

int main(){
	fprintf(stderr,"PPSubotto driver. v1.0\n");
	drive_printer("/dev/parport0");
	return EXIT_SUCCESS;
}
