package tests.androguard;


public class TestLoops {
	
	protected static class Loop {
		public static int i;
		public static int j;
	}
	
	public void aWhile( ) {
		int i = 5, j = 10;
		while( i < j ) {
			j += i / 2.0 + j;
			i += i * 2;
		}
		Loop.i = i;
		Loop.j = j;
	}

	public void aFor( ) {
		int i, j;
		for( i = 5, j = 10; i < j; i += i * 2 ) {
			j += i / 2.0 + j;
		}
		Loop.i = i;
		Loop.j = j;
	}
	
	public void aDoWhile( ) {
		int i = 5, j = 10;
		do
		{
			j += i / 2.0 + j;
			i += i * 2;
		} while( i < j );
		Loop.i = i;
		Loop.j = j;
	}
}
