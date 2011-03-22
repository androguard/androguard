package org.t0t0.android;

import android.app.Activity;
import android.os.Bundle;

public class TestCaseActivity extends Activity
{
    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        TestCase1 tc1 = new TestCase1();
    }
}
