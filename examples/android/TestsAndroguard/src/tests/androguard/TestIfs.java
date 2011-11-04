package tests.androguard;

public class TestIfs {
	private boolean P, Q, R, S, T;

	public static int testIF( int p ) {
		int i;
		
		if ( p > 0 ) {
			i = p * 2;
		} else {
			i = p + 2;
		}
		return i;
	}
	
	public static int testIF2( int p ) {
		int i = 0;
		
		if ( p > 0 ) {
			i = p * 2;
		} else {
			i = p + 2;
		}
		return i;
	}
	
	public static int testShortCircuit( int p ) {
		int i = 0;
		if ( p > 0 && p % 2 == 3 ) {
			i = p + 1;
		} else {
			i = -p;
		}
		return i;
	}
	
	public static int testShortCircuit2( int p ) {
		int i = 0;
		if ( p <= 0 || p % 2 != 3 )
			i = -p;
		else
			i = p + 1;
		return i;
	}
	
	public void testCFG( ) {
		int I = 1, J = 1, K = 1, L = 1;
		
		do {
			if ( P ) {
				J = I;
				if ( Q )
					L = 2;
				else L = 3;
				K++;
			} else {
				K += 2;
			}
			System.out.println(I + "," + J + "," + K + "," + L);
			do {
				if ( R )
					L += 4;
			} while ( !S );
			I += 6;
		} while ( !T );
	}
}
