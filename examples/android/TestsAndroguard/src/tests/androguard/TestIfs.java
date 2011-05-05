package tests.androguard;

public class TestIfs {

	public static int IF( int p ) {
		int i;
		
		if ( p > 0 ) {
			i = p * 2;
		} else {
			i = p + 2;
		}
		return i;
	}
	
	public static int IF2( int p ) {
		int i = 0;
		
		if ( p > 0 ) {
			i = p * 2;
		} else {
			i = p + 2;
		}
		return i;
	}
}
