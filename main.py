import pyopenpose as op
import sys
import os
import cv2
import time
import struct
import socket
import argparse

class Network:
    def __init__(self, ip, port):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((ip, port))
        self.serverSocket.listen(5)
        print('Listening')
        self.clientSocket, self.clientAddress = self.serverSocket.accept()
        print(self.clientAddress)

    def sendInt(self, data):
        self.clientSocket.send(struct.pack('I', data))

    def sendFloat(self, data):
        self.clientSocket.send(struct.pack('f', data))

    def sendPoseKeypoints(self, keypoints):
        self.sendInt(len(keypoints))
        for person in keypoints:
            self.sendInt(len(person))
            for keypoint in person:
                self.sendFloat(keypoint[0])
                self.sendFloat(keypoint[1])
                self.sendFloat(keypoint[2])

    def sendHandKeypoints(self, keypoints):
        self.sendInt(len(keypoints))
        for hand in keypoints:
            self.sendInt(len(hand[0]))
            for keypoint in hand[0]:
                self.sendFloat(keypoint[0])
                self.sendFloat(keypoint[1])
                self.sendFloat(keypoint[2])

class PoseDetector:
    def __init__(self):
        params = dict()
        params["model_folder"] = "models/"
        params["hand"] = True

        self.opWrapper = op.WrapperPython()
        self.opWrapper.configure(params)
        self.opWrapper.start()
        self.datum = op.Datum()

    def run(self, frame):
        self.datum.cvInputData = frame
        self.opWrapper.emplaceAndPop([self.datum])
        return self.datum.cvOutputData, self.datum.poseKeypoints, self.datum.handKeypoints


def update_arm(left_elbow, left_wrist, right_elbow, right_wrist):
    if left_wrist[1] > right_wrist[1]:
        return 2
    return 3

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, required=True)
    parser.add_argument('--no_network', default=False)
    parser.add_argument("--no_display", default=False)
    parser.add_argument('--output_position', type=str)
    parser.add_argument('--output_video', type=str)
    args = parser.parse_args()

    cap = None
    if args.video == '0':
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(args.video)
    
    poseDetector = PoseDetector()

    if not args.no_network:
        network = Network('127.0.0.1', 1234)

    print('running', flush=True)

    f_position = None
    if args.output_position is not None:
        f_position = open(args.output_position, 'w')
    
    if args.output_video is not None:
        video_writer = cv2.VideoWriter(args.output_video, cv2.VideoWriter_fourcc(*'XVID'), cap.get(5), (int(cap.get(3)), int(cap.get(4))))


    current_arm = 1
    current_pos = (0, 0)

    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        output, poseKeypoints, handKeypoints = poseDetector.run(frame)


        if args.output_position is not None:
            try:
                if len(poseKeypoints) > 0:
                    f_position.write(str(len(poseKeypoints)))
                    maxLength = 0
                    maxPos = 0
                    for person in poseKeypoints:
                        if (person[1][0] > 1 and person[8][0] > 1):
                            bodyX = (person[1][0] + person[8][0]) / 2
                            bodyY = (person[1][1] + person[8][1]) / 2
                            length = (person[1][0] - person[8][0]) * (person[1][0] - person[8][0]) + (person[1][1] - person[8][1]) * (person[1][1] - person[8][1])
                            if length > maxLength:
                                current_arm = update_arm(person[3], person[4], person[6], person[7])
                                maxLength = length
                                maxPos = (bodyX, bodyY)
                            cv2.circle(output, (int(bodyX), int(bodyY)), 4, (255, 0, 0), 0)
                            f_position.write(' ' + str(bodyX) + ' ' + str(bodyY))
                        else:
                            f_position.write(' 0.0 0.0')
                    current_pos = maxPos
                    f_position.write('\n')
                else:
                    f_position.write('0\n')
            except:
                pass

        if not args.no_network:
            network.sendInt(current_arm)
            print(current_arm, current_pos)
            network.sendFloat(current_pos[0])
            network.sendFloat(current_pos[1])
            
            '''
            try:
                if len(poseKeypoints) > 0:
                    network.sendPoseKeypoints(poseKeypoints)
                    pass
                if len(handKeypoints) > 0:
                    network.sendHandKeypoints(handKeypoints)
                    pass
            except:
                network.sendPoseKeypoints([])
            '''

        if not args.no_display:
            cv2.imshow("OpenPose", output)
            cv2.waitKey(10)
        
        if args.output_video is not None:
            video_writer.write(output)


    cap.release()
    cv2.destroyAllWindows()
    if args.output_video is not None:
        video_writer.release()