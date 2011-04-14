package tests.androguard;

import android.app.Activity;
import android.os.Bundle;

public class TestActivity extends Activity {
	public int value;
	public int value2;

	public TestActivity() {
		value = 100;
		value2 = 200;
	}
	
	public TestActivity( int value, int value2 ) {
		this.value = value;
		this.value2 = value2;
	}

	public int test_base(int _value, int _value2) {
		int y = 0;
		double sd = -6;
		double zz = -5;
		double yy = -4;
		double xx = -3;
		double w = -2;
		double x = -1;
		double k = 0.0;
		double d = 1;
		double b = 2;
		double c = 3;
		double f = 4;
		double z = 5;
		double cd = 6;
		float g = 4.20f;

		double useless = g * c + b - y + d;

		System.out.println("VALUE = " + this.value + " VALUE 2 = "
				+ this.value2);

		for (int i = 0; i < (_value + _value2); i++) {
			y = this.value + y - this.value2;
			y = y & 200 * test1(20);

			y = this.value2 - y;
		}

		try {
			int[] t = new int[5];
			t[6] = 1;
		} catch (java.lang.ArrayIndexOutOfBoundsException e) {
			System.out.println("boom");
		}

		if (this.value > 0) {
			this.value2 = y;
		}

		switch (this.value) {
		case 0:
			this.value2 = this.pouet();
			break;
		default:
			this.value2 = this.pouet2();
		}

		switch (this.value) {
		case 1:
			this.value2 = this.pouet();
			break;
		case 2:
			this.value2 = this.pouet2();
			break;
		case 3:
			this.value2 = this.pouet3();
		}

		return y;
	}

	public int foo(int i, int j) {
		while (true) {
			try {
				while (i < j)
					i = j++ / i;
			} catch (RuntimeException re) {
				i = 10;
				continue;
			}
			if (i == 0)
				break;
		}
		return j;
	}

	public int foo2(int i, int j) {
		while (i < j) {
			try {
				i = j++ / i;
			} catch (RuntimeException re) {
				i = 10;
			}
		}
		return j;
	}

	public int test1(int val) {
		int a = 0x10;

		return val + a - 60 * this.value;
	}

	public int pouet() {
		int v = this.value;
		return v;
	}

	public void test() {
		int a = this.value * 2;
		int b = 3;
		int c = 4;
		int d = c + b * a - 1 / 3 * this.value;
		int e = c + b - a;
		int f = e + 2;
		int g = 3 * d - c + f - 8;
		int h = 10 + this.value + a + b + c + d + e + f + g;
		int i = 150 - 40 + 12;
		int j = h - i + g;
		int k = 10;
		int l = 5;
		int m = 2;
		int n = 10;
		int o = k * l + m - n * this.value + c / e - f * g + h - j;
		int p = a + b + c;
		int q = p - k + o - l;
		int r = a + b - c * d / e - f + g - h * i + j * k * l - m - n + o / p
				* q;
		System.out.println(" meh " + r);
		this.test();
		this.test1(10);
		pouet2();
		this.pouet2();
		int s = pouet2();
	}

	public static void testDouble() {
		double f = -5;
		double g = -4;
		double h = -3;
		double i = -2;
		double j = -1;
		double k = 0;
		double l = 1;
		double m = 2;
		double n = 3;
		double o = 4;
		double p = 5;

		long ff = -5;
		long gg = -4;
		long hh = -3;
		long ii = -2;
		long jj = -1;
		long kk = 0;
		long ll = 1;
		long mm = 2;
		long nn = 3;
		long oo = 4;
		long pp = 5;

		float fff = -5;
		float ggg = -4;
		float hhh = -3;
		float iii = -2;
		float jjj = -1;
		float kkk = 0;
		float lll = 1;
		float mmm = 2;
		float nnn = 3;
		float ooo = 4;
		float ppp = 5;

		double abc = 65534;
		double def = 65535;
		double ghi = 65536;
		double jkl = 65537;

		double mno = 32769;
		double pqr = 32768;
		double stu = 32767;
		double vwx = 32766;

		long aabc = 65534;
		long adef = 65535;
		long aghi = 65536;
		long ajkl = 65537;

		long amno = 32769;
		long apqr = 32768;
		long astu = 32767;
		long avwx = 32766;

		float babc = 65534;
		float bdef = 65535;
		float bghi = 65536;
		float bjkl = 65537;

		float bmno = 32769;
		float bpqr = 32768;
		float bstu = 32767;
		float bvwx = 32766;

		double abcd = 5346952;
		long dcba = 5346952;
		float cabd = 5346952;

		double zabc = 65534.50;
		double zdef = 65535.50;
		double zghi = 65536.50;
		double zjkl = 65537.50;

		double zmno = 32769.50;
		double zpqr = 32768.50;
		double zstu = 32767.50;
		double zvwx = 32766.50;

		float xabc = 65534.50f;
		float xdef = 65535.50f;
		float xghi = 65536.50f;
		float xjkl = 65537.50f;

		float xmno = 32769.50f;
		float xpqr = 32768.50f;
		float xstu = 32767.50f;
		float xvwx = 32766.50f;
		
		float ymno = -5f;
		float ypqr = -65535f;
		float ystu = -65536f;
		float yvwx = -123456789123456789.555555555f;
		double yvwx2 = -123456789123456789.555555555;
		int boom = -606384730;
		float reboom = -123456790519087104f;
		float gettype = boom + 2 + 3.5f;
	}

	public static void bla() {
		System.out.println("k");
	}

	public int pouet2() {
		synchronized (this) {
			System.out.println("test");
		}
		return 90;
	}

	public int pouet3() {
		return 80;
	}

	public int go() {
		System.out.println(" test_base(500, 3) " + this.test_base(500, 3));

		return 0;
	}

	/** Called when the activity is first created. */
	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.main);
	}
}