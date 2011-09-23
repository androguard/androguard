package tests.androguard;


public class TestLoops {
	
	protected static class Loop {
		public static int i;
		public static int j;
	}
	
	public void testWhile( ) {
		int i = 5, j = 10;
		while( i < j ) {
			j += i / 2.0 + j;
			i += i * 2;
		}
		Loop.i = i;
		Loop.j = j;
	}

	public void testFor( ) {
		int i, j;
		for( i = 5, j = 10; i < j; i += i * 2 ) {
			j += i / 2.0 + j;
		}
		Loop.i = i;
		Loop.j = j;
	}
	
	public void testDoWhile( ) {
		int i = 5, j = 10;
		do
		{
			j += i / 2.0 + j;
			i += i * 2;
		} while( i < j );
		Loop.i = i;
		Loop.j = j;
	}
	
	public int testNestedLoops( int a )
	{
		if ( a > 1000 ) {
			return testNestedLoops( a / 2 );
		}
		else {
			while( a > 0 ) {
				a += 1;
				while ( a % 2 == 0 ) {
					a *= 2;
					while ( a % 3 == 0 ) {
						a -= 3;
					}
				}
			}
		}
		return a;
	}
	
	public void testMultipleLoops( )
	{
		int a = 0;
		while ( a < 50 )
			a += 2;
		while ( a % 3 == 0 )
			a *= 5;
		while ( a < 789 && a > 901 )
			System.out.println("woo");
	}

    public int testDoWhileTrue( int n )
    {
        do {
            n--;
            if ( n == 2 )
                return 5;
            if ( n < 2 )
                n = 500;
        } while( true );
    }

    public int testWhileTrue( int n )
    {
        while ( true ) {
            n--;
            if ( n == 2 )
                return 5;
            if ( n < 2 )
                n = 500;
        }
    }

    public int testDiffWhileDoWhile( int n )
    {
        while ( n != 2 ) {
            if ( n < 2 )
                n = 500;
        }
        return 5;
    }
}
