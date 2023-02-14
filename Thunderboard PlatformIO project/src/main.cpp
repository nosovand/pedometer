#include <mbed.h>
#include <string>
#include "ICM20648.h" // 6-axis inertial sensor
 
UnbufferedSerial serial_port(USBTX, USBRX, 115200);
DigitalOut R_LED(LED0); // LED0 = PD8 ~ RED, LED1 = PD9 ~ GREEN
DigitalOut G_LED(LED1);
DigitalIn B_1(BUTTON1);
DigitalIn B_2(BUTTON2);
/* Turn on power to IMU */
DigitalOut imu_en(PF8, 1);

//IMU VALUES
bool imu_enabled = true;

typedef struct imu_data{
    float sample, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z;
};
 
bool startReading = 0;

 void serial_isr()
{
    char c;
    if (serial_port.read(&c, 1))
    {  
        if(c == 's'){
            startReading = 1;
        }
    }
}

int main()
{
    thread_sleep_for(100);
   
    ICM20648* imu = new ICM20648(PC0, PC1, PC2, PC3, PF12);
    if(!imu->open()) {
        printf("Something is wrong with ICM20648, disabling...\n");
        imu_en = false;
    }

    imu->set_sample_rate(100);
    
    imu_data gyroData;

    serial_port.attach(serial_isr, SerialBase::RxIrq);

float acc_vector;

    while(1) {
            thread_sleep_for(20);
            imu->get_accelerometer(&gyroData.acc_x, &gyroData.acc_y, &gyroData.acc_z);
            acc_vector = (gyroData.acc_x * gyroData.acc_x) + (gyroData.acc_y * gyroData.acc_y) + (gyroData.acc_z * gyroData.acc_z);  
            serial_port.write(&acc_vector, sizeof(acc_vector)); 

    }
}