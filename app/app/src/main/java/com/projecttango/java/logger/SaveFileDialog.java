package com.projecttango.java.logger;

import android.app.AlertDialog;
import android.content.Context;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.ProgressBar;

/**
 * Displays progress bar and text information while saving an adf.
 *
 * Created by iida on 20170606.
 */
public class SaveFileDialog extends AlertDialog {
    private static final String TAG = SaveFileDialog.class.getSimpleName();
    private ProgressBar mProgressBar;

    public SaveFileDialog(Context context) {
        super(context);
    }

    public void setProgress(int progress) {
        if (mProgressBar != null) {
            mProgressBar.setVisibility(View.VISIBLE);
            mProgressBar.setProgress(progress);
        }
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.save_file_dialog);
        setCancelable(false);
        mProgressBar = (ProgressBar) findViewById(R.id.progress_bar);
        if (mProgressBar == null) {
            Log.e(TAG, "Unable to find view progress_bar.");
        }
    }
}
