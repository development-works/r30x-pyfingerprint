from serial import Serial
import time
from PIL import Image

HEADER = bytes.fromhex('EF01')

PID_COMMAND = bytes.fromhex('01')
PID_ACK = bytes.fromhex('07')
PID_DATA = bytes.fromhex('02')
PID_EOD = bytes.fromhex('08')

IC_VERIFY_PASSWORD = bytes.fromhex('13')
IC_GENERATE_IMAGE = bytes.fromhex('01')
IC_DOWNLOAD_IMAGE = bytes.fromhex('0a')
IC_GENERATE_CHARACTERISTICS = bytes.fromhex('02')
IC_GENERATE_TEMPLATE = bytes.fromhex('05')
IC_DOWNLOAD_CHAR_BUFFER = bytes.fromhex('08')
IC_SET_ADDRESS = bytes.fromhex('15')
IC_SET_PORT_CONTROL = bytes.fromhex('17')
IC_READ_TEMPLATE_NUM = bytes.fromhex('1d')
IC_AUTO_FINGERPRINT_VERIFICATION = bytes.fromhex('34')

CC_SUCCESS = bytes.fromhex('00')
CC_ERROR = bytes.fromhex('01')
CC_WRONG_PASS = bytes.fromhex('13')
CC_FINGER_NOT_DETECTED = bytes.fromhex('02')
CC_FAILED_TO_COLLECT_FINGER = bytes.fromhex('03')
CC_FAILED_DOWNLOAD_IMAGE = bytes.fromhex('0e')
CC_DISORDERED_FINGERPRINT = bytes.fromhex('06')
CC_VERY_SMALL_FINGERPRINT = bytes.fromhex('07')
CC_INVALID_PRIMARY_IMAGE = bytes.fromhex('15')
CC_CHAR_MISMATCH = bytes.fromhex('0a')
CC_TEMPLATE_DWNLD_ERR = bytes.fromhex('0d')
CC_FAILED_TO_OPERATE_PORT = bytes.fromhex('1d')
CC_NO_MATCHING_FINGERPRINT = bytes.fromhex('09')

CHAR_BUFFER_1 = bytes.fromhex('01')
CHAR_BUFFER_2 = bytes.fromhex('02')


class Sensor:
    def __init__(self, port, baudrate):
        self._serial = Serial(port, baudrate=baudrate, timeout=3)
        self._password = bytes.fromhex('00000000')
        self._address = bytes.fromhex('FFFFFFFF')

        self.__verify_password()

    def __verify_password(self):
        """

        :return:
        """
        cc = self.__send_command(IC_VERIFY_PASSWORD, self._password);

        if cc == CC_SUCCESS:
            print("Verified")
        elif cc == CC_ERROR:
            raise Exception("error when receiving package")
        elif cc == CC_WRONG_PASS:
            raise Exception("Wrong Password")
        else:
            raise Exception("Unrecognised confirmation code")

    def generate_image(self):
        """

        :return:
        """
        time.sleep(2)
        cc = self.__send_command(IC_GENERATE_IMAGE)

        if cc == CC_SUCCESS:
            print("Finger Collection Success")
        elif cc == CC_ERROR:
            raise Exception("error when receiving package")
        elif cc == CC_FINGER_NOT_DETECTED:
            raise Exception("can’t detect finger")
        elif cc == CC_FAILED_TO_COLLECT_FINGER:
            raise Exception("fail to collect finger;")
        else:
            raise Exception("Unrecognised confirmation code")

    def download_image(self):
        """

        :return:
        """
        cc = self.__send_command(IC_DOWNLOAD_IMAGE);

        if cc == CC_SUCCESS:
            print("Downloading the fingerprint image")
        elif cc == CC_ERROR:
            raise Exception("error when receiving package for downloading "
                            "image")
        elif cc == CC_FAILED_DOWNLOAD_IMAGE:
            raise Exception("Could not download image")
        else:
            raise Exception("Unrecognised confirmation code")

        image_rcv = bytes()

        with open('temp/img.jpg', 'ab') as file:
            while True:
                pid_rcv, content_rcv = self.__receive_packet()
                image_rcv = image_rcv + content_rcv

                if pid_rcv == PID_EOD:
                    print("End of Data reached")
                    break

        # TODO: Save the File in image form

        # finger_img = Image.frombytes("L", (256, 288), image_rcv)
        # finger_img.save("./temp/FingerPrintImage.jpg")

    def generate_charfile_image(self, buffer_id):
        """

        :param buffer_id:
        :return:
        """
        cc = self.__send_command(IC_GENERATE_CHARACTERISTICS, buffer_id);

        if cc == CC_SUCCESS:
            print("generate character file complete;")
        elif cc == CC_ERROR:
            raise Exception("error when receiving package for downloading "
                            "image")
        elif cc == CC_DISORDERED_FINGERPRINT:
            raise Exception("fail to generate character file due to the "
                            "over-disorderly fingerprint image")
        elif cc == CC_VERY_SMALL_FINGERPRINT:
            raise Exception("fail to generate character file due to lackness "
                            "of character point or over-smallness of "
                            "fingerprint image")
        elif cc == CC_INVALID_PRIMARY_IMAGE:
            raise Exception("fail to generate the image for the lackness of "
                            "valid primary image")
        else:
            raise Exception("Unrecognised confirmation code")

    def generate_template(self):
        """

        :return:
        """
        cc = self.__send_command(IC_GENERATE_TEMPLATE);

        if cc == CC_SUCCESS:
            print("generate template complete")
        elif cc == CC_ERROR:
            raise Exception("error when receiving package for downloading "
                            "image")
        elif cc == CC_CHAR_MISMATCH:
            raise Exception("fail to combine the character files. That’s, "
                            "the character files don’t belong to one finger")
        else:
            raise Exception("Unrecognised confirmation code")

    def download_char_buffer(self, buffer_id):
        """

        :param buffer_id:
        :return:
        """
        # self.__send_packet(PID_COMMAND, IC_DOWNLOAD_CHAR_BUFFER + buffer_id)
        # pid_rcv, content_rcv = self.__receive_packet()

        cc = self.__send_command(IC_DOWNLOAD_CHAR_BUFFER, buffer_id);

        if cc == CC_SUCCESS:
            print("Downloading the fingerprint image")
        elif cc == CC_ERROR:
            raise Exception("error when receiving package for downloading "
                            "image")
        elif cc == CC_TEMPLATE_DWNLD_ERR:
            raise Exception("Error when downloading template")
        else:
            raise Exception("Unrecognised confirmation code")

        char_rcv = bytes()

        while True:
            pid_rcv, content_rcv = self.__receive_packet()
            char_rcv = char_rcv + content_rcv

            if pid_rcv == PID_EOD:
                print("End of Data reached")
                break

        print(char_rcv)

    def __checksum(self, pid, package_len, content):
        """

        :param pid:
        :param package_len:
        :param content:
        :return:
        """
        checksum = int.from_bytes(pid, byteorder='big') + package_len

        # Addition of individual bytes in content as otherwise int conversion
        # will not make sense
        for byte in content:
            checksum = checksum + byte

        checksum = checksum & 0xFFFF

        # 0xFFFF - to remove exception in case checksum is greater than 2
        # bytes
        #      1111 1111 1111 1111
        # 0001 0011 0011 1011 1001 - Checksum
        #      0011 0011 1011 1001 - result
        return checksum.to_bytes(2, byteorder='big')

    def __send_packet(self, pid, content):
        """

        :param pid:
        :param content:
        :return:
        """
        package_len = len(content) + 2

        checksum = self.__checksum(pid, package_len, content)
        # Getting value of checksum

        self._serial.write(HEADER)
        self._serial.write(self._address)
        self._serial.write(pid)
        self._serial.write(package_len.to_bytes(2, byteorder='big'))
        self._serial.write(content)
        self._serial.write(checksum)

    def __receive_packet(self):
        """

        :return:
        """
        header_rcv = self._serial.read(2)
        if header_rcv != HEADER:
            raise Exception("Acknowledgment Header invalid")

        address_rcv = self._serial.read(4)
        if address_rcv != self._address:
            raise Exception("Address is invalid")

        pid_rcv = self._serial.read(1)
        '''if pid_rcv != PID_ACK:
            raise Exception("PID is invalid")'''

        len_rcv = self._serial.read(2)
        len_rcv = int.from_bytes(len_rcv, byteorder='big')

        content_rcv = self._serial.read(len_rcv - 2)

        checksum_rcv = self._serial.read(2)
        if checksum_rcv != self.__checksum(pid_rcv, len_rcv, content_rcv):
            raise Exception("Checksum Mismatch")

        return pid_rcv, content_rcv

    def __send_command(self, command, *args):
        """

        :param command: bytes
        :param args: other parameters for the command
        :return:
        """
        data = command
        for arg in args:
            data += arg

        self.__send_packet(PID_COMMAND, data)
        pid, cc = self.__receive_packet()

        if pid != PID_ACK:
            raise Exception("Received packet in not an acknowledgement packet")

        return cc

    # Set Password - D

    # Set Module Address - A
    def set_address(self, address):
        if len(address) != 4:
            raise Exception("Invalid Address Length")

        cc = self.__send_command(IC_SET_ADDRESS, address)

        if cc == CC_SUCCESS:
            print("Password set successfully")
        else:
            raise Exception("Unable to set password, cc = " + str(cc))

    # Set module system's basic parameter - D

    # Port Control - A
    def set_port_control(self, val):
        """

        :param val, bool:
        :return:
        """
        zero = int(0).to_bytes(1, byteorder='big')
        one = int(1).to_bytes(1, byteorder='big')

        cc = self.__send_command(IC_SET_PORT_CONTROL, one if val else zero)

        if cc == CC_SUCCESS:
            print("port control set successfully")
        if cc == CC_ERROR:
            print("Error when receiving packet")
        elif cc == CC_FAILED_TO_OPERATE_PORT:
            raise Exception("Failed to operate communication port")

    # Read system Parameter - D

    # Read valid template number - A
    def read_valid_template_num(self):
        data = self.__send_command(IC_READ_TEMPLATE_NUM)
        cc = data[0:1]
        template_num = data[1:]
        if cc == CC_SUCCESS:
            return template_num
        if cc == CC_ERROR:
            raise Exception("Error when receiving package")
        else:
            raise Exception("Invalid cc")

    # upload image - D

    # upload character file or template - A


    # To store template - D

    # To Read template from flash library - A

    # To delete template - D

    # To empty finger library - A

    # To carry out precise matching of two fingerprint template - D

    # To search finger library - A

    # To Generate a random code - D

    # To Write Notepad - A

    # To Read Notepad - D


sensor = Sensor('/dev/ttyUSB0', 57600)
# sensor.generate_image()
# sensor.download_image()
# sensor.generate_charfile_image(CHAR_BUFFER_1)
# sensor.generate_charfile_image(CHAR_BUFFER_2)
# sensor.generate_template()
# sensor.download_char_buffer(CHAR_BUFFER_1)
# print(sensor.read_valid_template_num())
print(sensor.auto_fingerprint_verification())