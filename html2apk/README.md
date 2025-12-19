
from https://ssb22.user.srcf.net/indexer/html2apk.html (also [mirrored on GitLab Pages](https://ssb22.gitlab.io/indexer/html2apk.html) just in case)

# Android viewer app for static HTML

This is a method for making a standalone Android “app” from a collection of static HTML and Javascript files, such as files from [Offline HTML Indexer](../README.md) or Charlearn mobile. Apps made using the files below should run on any version of Android (v1+), and extra Javascript functions are provided to place text on the Android clipboard.

Packaging an offline site as an app makes it easier for beginners to install, but it does mean the app will not automatically copy any “accessibility” options that were set in the main browser. This app will make some attempt to compensate (and it includes `setZoomLevel` code from Annotator Generator if you need to make a custom zoom control), but for maximum accessibility you should always ship an alternative version of your HTML that is *not* packaged as an app.

If your app uses “local storage”, this requires Android 2.1+ (you can use `localStorage.setItem` etc in scripts; ‘cookies’ tend not to work).

UTF-8 encoding is assumed.

## Instructions for old Android Developer Tools

In June 2015 Google deprecated the Android Developer Tools (ADT), and in June 2017 removed the download, saying “you should immediately switch” to the newer Android Studio. Since Android Studio does not work on all equipment, you might find these instructions for the older ADT useful if you happen to have downloaded it before June 2017 (although I do suggest checking if your older equipment can at least host a virtual machine with a suitable GNU/Linux installation to run Android Studio). App updates compiled in old ADT have been rejected by Google’s “Play Store” since 2018 and may not be “side-loadable” after Android 10, plus you’ll have to remove dark-mode code from `styles.xml` if compiling on old ADT.
* The method described on this page worked in ADT versions 21.0.1 and 22.2.1, but it did **not** work in 23.0.2: perhaps due to an installer bug, the copy of 23.0.2 I tried refused to build any new projects, although it was still able to build projects that had been created earlier.
1. In ADT, go to File / New / Android application project
2. Enter the following information:
   * Application Name: Any short name you wish (will be shown in the phone’s app menu)
   * Project Name: anything you want (just needs to be unique on your development computer)
   * Package Name: `org.ucam.ssb22.html`
   * Minimum Required SDK: API 1: Android 1.0
     **or** API 7 if you use local storage
3. Leave everything else as default, but make a note of the project directory (probably mentioned on the second setup screen as “location”)
4. Switch out of ADT, and copy this `html2apk` directory into the project directory (overwriting 2 files)
5. If you use local storage, edit `src/org/ucam/ssb22/html/MainActivity.java` and uncomment the lines as instructed
6. (Optional) If you don’t want your app to be reloaded with every screen or keyboard change, edit the top-level `AndroidManifest.xml` file and after `<activity` put `android:configChanges="orientation|screenSize|keyboardHidden"` (you will likely need to re-start the ADT after saving this edit)
7. If you are distributing your app to others, or if you intend to load more than one HTML-based app onto your device, please **change the package name** (in `AndroidManifest.xml` and `MainActivity.java`, and by renaming the directories under `src`) to a (sub)domain you own. This is needed because, if another application already on the device has the same package name, then installing yours will **overwrite** the one that’s already there and vice versa. (But if you change the package name when the app is already deployed, attempts to install the new version will leave the previous version on the device *as well*.)
8. Place your HTML (and any related files) into the `assets` subdirectory, with `index.html` as the starting page
9. Back in ADT, go to Run / Run As / Android application. It should let you launch a virtual Android device. It’s probably best not to interact with the virtual Android device until the ADT has finished setting it up (check for messages in ADT’s Console window). If the install fails, try Run again.
10. If the install is successful, then you should see your application running when you unlock the Android device in the emulator.
11. The .apk file will have by this time been placed in the `bin` subdirectory of the project directory. This file can be copied to a Web server and linked to. (A connection will be required for installing from the Web, but not for usage later.) **It might be necessary to go to “Application settings” or “Security” and enable “Unknown sources”** before the app will install on a real phone.

## Command line

Command-line builds are easier to automate, and also work if you’ve upgraded to the newer Android Studio—you just need to make sure the directories are set correctly for SDK etc. There is an example script [compile.sh](compile.sh)—don’t forget to change the variables at the beginning, and to change the package name in other files as described above.

## Copyright and Trademarks
All material © Silas S. Brown unless otherwise stated.
Android is a trademark of Google LLC.
Google is a trademark of Google LLC.
Javascript is a trademark of Oracle Corporation in the US.
Linux is the registered trademark of Linus Torvalds in the U.S. and other countries.
Any other trademarks I mentioned without realising are trademarks of their respective holders.
