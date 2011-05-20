package tests.androguard;

public class TestArr$ays {
	
	public static class InternField {
		public static byte[] b;
	}

	private byte[] b;
	public byte[] d;
	
	public TestArr$ays( ) {
		b = new byte[5];
	}
	
	public TestArr$ays( byte [] b ) {
		this.b = b;
	}
	
	public TestArr$ays( int i ) {
		byte [] a = { 1, 2, 3, 4, 5 };
		b = a;
	}
	
	public void emptyArrayByte( ) {
		byte [] b = new byte[5];
		InternField.b = b;
	}
	
	public void fullArrayByte( ) {
		byte[] b = { 1, 2, 4, 39, 20 };
		this.b = b;
	}
	
	public void modifArrayByte( ) {
		b[2000000] = 2;
	}
	
	public void instanceInternArrayByte( ){
		InternField f = new InternField();
		f.b = new byte[5];
		f.b[2] = 40;
	}
}
