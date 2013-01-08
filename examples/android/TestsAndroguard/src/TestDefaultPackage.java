
public class TestDefaultPackage {

	private class TestInnerClass {
		private int a, b;

		private TestInnerClass(int a, int b)
		{
			this.a = a;
			this.b = b;
		}
		
		public void Test(int d)
		{
			System.out.println("Test2: " + this.a + d + this.b);
		}

		private class TestInnerInnerClass {
			private int a, c;
			
			private TestInnerInnerClass(int a, int c)
			{
				this.a = a;
				this.c = c;
			}
			
			public void Test(int b)
			{
				System.out.println("Test: " + this.a * b + this.c);
			}
		}
	}
	
	public static void main(String [] z)
	{
		TestDefaultPackage p = new TestDefaultPackage();
		TestInnerClass t = p.new TestInnerClass(3, 4);
		TestInnerClass.TestInnerInnerClass t2 = t.new TestInnerInnerClass(3, 4);
		System.out.println("t.a = " + t.a);
	}
}
