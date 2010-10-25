class Hello
{  
   public static void main(String args[])
   {
      System.out.println("Hello World!");    
   }

   public byte[] test(byte[] buf) 
   {
      return null;
   }

   public int test2() {
      return 10 + this.test4() & this.test3();
   }

   public int test3() {
      return 0xff;
   }

   public int test4() {
      return 0x1;
   }

   public int test5() {
      Byte x = 10;

      int REG[5];

      return (int)x;
   }
}

