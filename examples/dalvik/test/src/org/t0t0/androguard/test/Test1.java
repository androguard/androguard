package org.t0t0.androguard.test;                                               

public class Test1 {
    public int value;
    public int value2;
    
    public Test1() {
      this.value = 100;
      this.value2 = 200;
    }

    public int test_base(int value) {
      int y = 0;
      for(int i = 0; i < value; i++) {
         y = y + (y & this.test1(50)) + this.value;
      }

      return y;
    }

    public int test1(int val) {
      int a = 0x10;

      return val + a - 60;
    }

    public int go() {
      System.out.println(" test_base(500) " + this.test_base( 500 ) );

      return 0;
    }    
}
