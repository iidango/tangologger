package com.projecttango.java.logger;

import android.app.Activity;
import android.app.DialogFragment;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import com.google.atap.tangoservice.TangoAreaDescriptionMetaData;

/**
 * Queries the user for an ADF name, optionally showing the ADF UUID.
 *
 * Created by iida on 20170606.
 */
public class SetFileNameDialog extends DialogFragment {

    EditText mNameEditText;
    TextView mUuidTextView;
    CallbackListener mCallbackListener;
    Button mOkButton;
    Button mCancelButton;

    interface CallbackListener {
        void onFileNameOk(String name, String uuid);
        void onFileNameCancelled();
    }

    @Override
    public void onAttach(Activity activity) {
        super.onAttach(activity);
        mCallbackListener = (CallbackListener) activity;
    }

    @Override
    public View onCreateView(LayoutInflater inflator, ViewGroup container,
                             Bundle savedInstanceState) {
        View dialogView = inflator.inflate(R.layout.set_name_dialog, container, false);
        getDialog().setTitle(R.string.set_name_dialog_title);
        mNameEditText = (EditText) dialogView.findViewById(R.id.name);
        mUuidTextView = (TextView) dialogView.findViewById(R.id.uuidDisplay);
        setCancelable(false);
        mOkButton = (Button) dialogView.findViewById(R.id.ok);
        mOkButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                mCallbackListener.onFileNameOk(
                        mNameEditText.getText().toString(),
                        mUuidTextView.getText().toString());
                dismiss();
            }
        });
        mCancelButton = (Button) dialogView.findViewById(R.id.cancel);
        mCancelButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                mCallbackListener.onFileNameCancelled();
                dismiss();
            }
        });
        String name = this.getArguments().getString(TangoAreaDescriptionMetaData.KEY_NAME);
        String id = this.getArguments().getString(TangoAreaDescriptionMetaData.KEY_UUID);
        if (name != null) {
            mNameEditText.setText(name);
        }
        if (id != null) {
            mUuidTextView.setText(id);
        }
        return dialogView;
    }
}
