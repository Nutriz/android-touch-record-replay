#!/usr/bin/python3
import os
from argparse import ArgumentParser
import subprocess
import sys
import time
import re


class ParseCommandLine:
    usage_meg = """session_replay_data_usage apk activity
    apk: name of the Demo apk, example 'demoApp-release.apk'.
    activity: main activity, example 'com.contentsquare.android.demo/.main.ui.MainActivity'
    quality: Session replay quality should be LOW, MEDIUM or HIGH.
    architecture: Mac architecture, x86 or arm64.
    """

    @staticmethod
    def parse():
        parser = ArgumentParser(usage=ParseCommandLine.usage_meg)
        parser.add_argument("apk", help="Demo apk for the Session Replay data usage test")
        parser.add_argument("activity",
                            help="main activity, example 'com.contentsquare.android.demo/.main.ui.MainActivity'")
        parser.add_argument("quality", help="Session replay quality should be LOW, MEDIUM or HIGH.")
        parser.add_argument("architecture", help="Mac architecture, x86 or arm64")
        args = parser.parse_args()
        print("test apk={}, activity={}, quality={}, architecture={}".format(args.apk, args.activity, args.quality, args.architecture))
        print("/!\ Be sure to start one, and only one Pixel 2 emutator, with API level 28, before this script.")
        print("/!\ Be sure to start the Session Replay local player before this script.")
        print("/!\ Be sure that mysendevent-x86 or mysendevent-arm64 in android-touch-record-replay is executable.")
        return args


class AdbCommands:

    def __init__(self, args):
        self.task_id = 'unknown'
        self.apk = args.apk
        self.complete_activity_name = args.activity
        self.package = args.activity.split('/')[0]
        self.activity = args.activity.split('/')[1]
        self.quality = args.quality
        self.architecture = args.architecture

    def uninstall(self):
        print("\nUninstall: ", self.package)
        AdbCommands.checked_subprocess_call("adb uninstall {}".format(self.package),
                                            "not installed", False)
        return self

    def install(self):
        print("\nInstall: ", self.apk)
        AdbCommands.checked_subprocess_call("adb install -r -t {}".format(self.apk))
        return self

    def configure(self):
        print("\nConfigure SDK")
        AdbCommands.checked_subprocess_call(
            'adb shell am force-stop {} && adb shell "am start -W -a android.intent.action.VIEW -d cs-{}://contentsquare.com?activationKey=weballwin\&userId=iamjenkins\&configure="DEVELOPER_SESSION_REPLAY_URL=http://10.0.2.2:7014,SESSION_REPLAY_FORCE_START=true,VERBOSE_LOG=true""'.format(
                self.package, self.package), timeout=5)
        return self

    def force_quality(self):
        fps = 10
        image_quality = 2
        if self.quality == "LOW":
            fps = 5
            image_quality = 0
        elif self.quality == "MEDIUM":
            fps = 10
            image_quality = 1

        print("\nForce quality SDK")
        AdbCommands.checked_subprocess_call(
            'adb shell am force-stop {} && adb shell "am start -W -a android.intent.action.VIEW -d cs-{}://contentsquare.com?activationKey=weballwin\&userId=iamjenkins\&configure="DEVELOPER_SESSION_REPLAY_FORCE_QUALITY_LEVEL=true,DEVELOPER_SESSION_REPLAY_FPS_VALUE={},DEVELOPER_SESSION_REPLAY_IMAGE_QUALITY_VALUE={}""'.format(
                self.package, self.package, fps, image_quality), timeout=5)
        return self

    def disable_masking(self):
        print("\nDisable masking")
        AdbCommands.checked_subprocess_call(
            'adb shell am force-stop {} && adb shell "am start -W -a android.intent.action.VIEW -d cs-{}://contentsquare.com?activationKey=weballwin\&userId=iamjenkins\&configure="SESSION_REPLAY_DEFAULT_MASKING=false""'.format(
                self.package, self.package), timeout=5)
        return self

    def start(self):
        print("\nStart...", self.complete_activity_name)
        AdbCommands.checked_subprocess_call("adb shell am start -n {}".format(self.complete_activity_name))
        # waiting for the app start.
        time.sleep(5)
        return self

    def play(self):
        print("\nPlay...", self.complete_activity_name)
        AdbCommands.checked_subprocess_call(
            "./replay_touch_events.sh -{} recorded_touch_events_sr_test_scenario.txt".format(self.architecture))
        # waiting for the app start.
        time.sleep(5)
        return self

    @staticmethod
    def checked_subprocess_call(popenargs, error_msg="", exit_on_error=True, timeout=None):
        try:
            # Warning the time out is in second, not in millis seconds as the documentation said :'(
            result = subprocess.call(popenargs, timeout=timeout, shell=True)
            if result != 0:
                print("{}\n".format(error_msg))
                if exit_on_error:
                    sys.exit([result])
        except subprocess.TimeoutExpired:
            print("Time out.")


if __name__ == "__main__":
    argsParsed = ParseCommandLine().parse()
    AdbCommands(argsParsed).uninstall().install().configure().force_quality().disable_masking().start().play()
