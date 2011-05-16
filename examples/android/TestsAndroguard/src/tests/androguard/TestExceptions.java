package tests.androguard;


public class TestExceptions {
	
	public int Test1( int a )
	{
		try {
			a = 5 / 0;
		} catch ( ArithmeticException e ) {
			a = 3;
		}
		return a;
	}
	
	public static int Test2( int a, int b ) throws ArrayIndexOutOfBoundsException
	{
		int [] t = new int[b];
		
		if ( b == 10 )
			b++;
		
		for( int i = 0; i < b; i++ )
		{
			t[i] = 5;
		}
		
		return a + t[0];
	}
	
	public int Test3( int a, int[] t )
	{
		int result = 0;
		
		if ( a % 2 == 0 )
		{
			try {
				result = t[a];
			} catch (ArrayIndexOutOfBoundsException e) {
				result = 1337;
			}
		}
		else if ( a % 3 == 0 ) {
			result = a * 2;
		} else {
			result = t[0] - 10;
		}
		
		return result;
	}
	
	public static void tests( String [] z )
	{
		System.out.println( "Result test1 : " + new TestExceptions().Test1( 10 ) );
		
		System.out.println( "=================================" );
		try {
			System.out.println( "Result test2 : " + Test2( 5, 10 ) );
		} catch (ArrayIndexOutOfBoundsException e) {
			System.out.println( "Result test2 : " + Test2( 5, 9 ) );
		}
		
		System.out.println( "=================================" );
		int [] t = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };
		System.out.println( "Result test3 : " + new TestExceptions().Test3( 8, t ) );
		System.out.println( "Result test3 : " + new TestExceptions().Test3( 9, t ) );
		System.out.println( "Result test3 : " + new TestExceptions().Test3( 7, t ) );
	}
}
