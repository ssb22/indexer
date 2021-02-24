// Android HTML wrapper - Silas Brown 2013,2014 - Public Domain
// Version 1.4

// See website for setup instructions:
// http://ssb22.user.srcf.net/gradint/html2apk.html
// See comments in the code
// for details of the extra Javascript callbacks

package org.ucam.ssb22.html;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.JavascriptInterface;
import android.app.Activity;
import android.os.Bundle;
import android.view.KeyEvent;
import android.net.Uri;
import android.content.Intent;
import android.annotation.TargetApi;
import android.os.Build;
public class MainActivity extends Activity {
    @Override
    @TargetApi(3) // for conditional setBuiltInZoomControls below
    @SuppressWarnings("deprecation") // for conditional SDK below
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        browser = (WebView)findViewById(R.id.browser);
        browser.getSettings().setJavaScriptEnabled(true);

        // The following enables alerts:
        browser.setWebChromeClient(new WebChromeClient());
        
        float fs = getResources().getConfiguration().fontScale; // from device accessibility settings
        if (fs < 1.0f) fs = 1.0f;
        final float fontScale=fs*fs;

        // The following allows the system browser to
        // open for HTTP links and not for file links.
        // If you want the embedded browser to process
        // HTTP links as well, then always return false
        // and give the app Internet permission.
        // Otherwise it'll be up to the system which links
        // are processed in the embedded browser and which
        // are not (and can be overridden by apps like
        // Kingsoft WPS Office, so be careful; I suggest
        // leaving this code in here) -
        browser.setWebViewClient(new WebViewClient(){
                public boolean shouldOverrideUrlLoading(WebView view, String url) {
                    if (url != null && (url.startsWith("http://") || url.startsWith("https://"))) {
                        view.getContext().startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                        return true;
                    } else return false;
                }
            });

        /* Uncomment the following 2 lines if you want to
           use local storage.  Requires API 7 (Android 2.1). */
        // browser.getSettings().setDomStorageEnabled(true);
        // browser.getSettings().setDatabasePath(browser.getContext().getFilesDir().getPath()+"data/" + browser.getContext().getPackageName() + "/databases/");
        /* WARNING: Local storage might be erased when a
           new version of your app is installed.   */
        
        /* The following allows your Javascript to say
           clipboard.copy(text) which might be useful
          (also clipboard.append(text), clipboard.get() and
            clipboard.clear(), currently getting only OUR text) */
        class Clipboard {
            public Clipboard() {}
            @JavascriptInterface
            // @SuppressWarnings("deprecation") // no longer needed as it's above
            @TargetApi(11)
            public void copy(String text) {
                if(Integer.valueOf(Build.VERSION.SDK) < Build.VERSION_CODES.HONEYCOMB) // SDK_INT requires API 4 but this works on API 1
                    ((android.text.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).setText(text);
                else ((android.content.ClipboardManager)getSystemService(android.content.Context.CLIPBOARD_SERVICE)).setPrimaryClip(android.content.ClipData.newPlainText(text,text));
                lastCopied = text;
            }
            @JavascriptInterface
            public void append(String text) { copy(lastCopied + text); }
            @JavascriptInterface
            public String get() { return lastCopied; }
            @JavascriptInterface
            public void clear() { copy(""); }
            String lastCopied = "";
        }
        browser.addJavascriptInterface(new Clipboard(),"clipboard");

        class ZoomControls {
            public ZoomControls(MainActivity act) {
                this.act = act;
                if(canCustomZoom()) setZoomLevel(Integer.valueOf(getSharedPreferences("html2apk",0).getString("zoom", "4")));
            }
            MainActivity act; int zoomLevel;
            @JavascriptInterface public int getZoomLevel() { return zoomLevel; }
            final int[] zoomPercents = new int[] {65,72,81,90,100,110,121,133,146,161,177,194,214,235,259,285,313,345,379};
            @JavascriptInterface public int getZoomPercent() { return zoomPercents[zoomLevel]; }
            @JavascriptInterface public int getRealZoomPercent() { return Math.round(zoomPercents[zoomLevel]*fontScale); }
            @JavascriptInterface public int getMaxZoomLevel() { return zoomPercents.length-1; }
            @JavascriptInterface @TargetApi(14) public void setZoomLevel(final int level) {
                act.runOnUiThread(new Runnable(){
                    @Override public void run() {
                        browser.getSettings().setTextZoom(Math.round(zoomPercents[level]*fontScale));
                    }
                });
                android.content.SharedPreferences.Editor e;
                do { e = getSharedPreferences("html2apk",0).edit();
                     e.putString("zoom",String.valueOf(level));
                } while(!e.commit());
                zoomLevel = level;
            }
            @JavascriptInterface public boolean canCustomZoom() {
                return AndroidSDK >= 14;
            }
        }
        browser.addJavascriptInterface(new ZoomControls(this),"zoom");

        /* The following provides a Javascript object
           "audioplayer" - you can call
           "audioplayer.play(file)" for a file in the assets
           directory and it works around bugs in Android 4
           that stop HTML 5 Audio with local files.  Note
           this is for playing only SHORT audio - it's
           synchronous in the GUI thread. */
        class AudioPlayer {
            public AudioPlayer() {}
            @JavascriptInterface
            public void play(String file) throws java.io.IOException {
                if(Integer.valueOf(Build.VERSION.SDK) >= 15) {
                	// HTML 5 Audio won't work on 4.4, reportedly went wrong between 4.1.2 and 4.2.x.
                	// This alternative code crashed on 2.3.4, but tested OK on a 4.0.3 device.
                	// So let's switch to it at API 15 (=4.0.3)
            	java.io.InputStream is=getAssets().open(file); // from zipped apk
            	byte[] buf = new byte[is.available()]; is.read(buf); is.close();
            	java.io.FileOutputStream os=new java.io.FileOutputStream(new java.io.File(getCacheDir()+"/sound.mp3"));
            	os.write(buf); os.close();
            	android.media.MediaPlayer m=new android.media.MediaPlayer();
                	m.setDataSource(getCacheDir()+"/sound.mp3");
                	m.setAudioStreamType(android.media.AudioManager.STREAM_NOTIFICATION);
                    m.prepare();
                    int dur = m.getDuration();
            	m.start();
            	try { Thread.sleep(dur); } catch(InterruptedException e) {}
            	m.stop(); m.release();
                } else {
                	// Earlier APIs: use HTML 5 Audio
                	browser.loadUrl("javascript:var e=document.createElement('audio');e.setAttribute('src','file:///android_asset/"+file+"');e.play()");
                }
            }
        }
        browser.addJavascriptInterface(new AudioPlayer(),"audioplayer");

        /* The following enables pinch-to-zoom on API 3+
           (Android 1.5+), not available on earlier versions.
           Note that this zoom does NOT reflow the page in 4.4+ */
        if(Integer.valueOf(Build.VERSION.SDK) >= 3) {
            browser.getSettings().setBuiltInZoomControls(true);
        }
        /* and the following does a with-reflow resize according
           to the text size setting on the Accessibility options (all versions) */
        int size=Math.round(16*getResources().getConfiguration().fontScale);
        browser.getSettings().setDefaultFontSize(size);
        browser.getSettings().setDefaultFixedFontSize(size);
        /*  finally, assume UTF-8 and load index.html */
        browser.getSettings().setDefaultTextEncodingName("utf-8");
        browser.loadUrl("file:///android_asset/index.html");
    }
    @Override public boolean onKeyDown(int keyCode, KeyEvent event) {
        if ((keyCode == KeyEvent.KEYCODE_BACK) &&
            browser.canGoBack()) {
            browser.goBack(); return true;
        } else return super.onKeyDown(keyCode, event);
    }
    int AndroidSDK = (Build.VERSION.RELEASE.startsWith("1.") ? Integer.valueOf(Build.VERSION.SDK) : Build.VERSION.SDK_INT);
    WebView browser;
}
