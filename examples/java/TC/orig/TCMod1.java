public class TCMod1 {
   public int TC1 = 0;
   private int TC2 = 3;

   public String equal(int a, int b)
   {
      System.out.print(a + " " + b + " ---- ");
      if (a == b) {
         return "True";
      }

      return "False";
   }

   public TCMod1()
   {
      System.out.println("TC1 == 0 : " + this.equal( this.TC1, 0 ));
      System.out.println("TC2 == 3 : " + this.equal( this.TC2, 3 ));
      TC1 = 20;
      System.out.println("TC1 == 20 : " + this.equal( this.TC1, 20 ));
   }

   public void T1()
   {
      int i;
      for(i = 0; i < 30; i++)
      {
         this.TC1 += i;
      }
      System.out.println("TC1 == 455 : " + this.equal( this.TC1, 455 ));
   
      int j = 40;
      System.out.println("J == 40 : " + this.equal( j, 40 ));

      for(; j < 40000; j++);
      System.out.println("J == 40000 : " + this.equal( j, 40000 ));
      
      this.TC1 += j;
      System.out.println("TC1 == 40455 : " + this.equal( this.TC1, 40455 ));
   
      int k[][] = { { 40, 30 }, { 60000, -788 }, { -2344556, 10000 } };

      for(i = 0; i < k.length; i++) {
         for(j=0; j < k[i].length; j++) {
            this.TC1 += k[i][j];
         }
      }

      System.out.println("TC1 == -2234819 : " + this.equal( this.TC1, -2234819 ));
   
      i = 300; j =-188;
      System.out.println("I == 300 : " + this.equal( i, 300 ));
      System.out.println("J == -188 : " + this.equal( j, -188 ));

      do {
         this.TC2 += ( j - i );         
         j += 3;
         i -= 2;
      } while ( j < i );
      System.out.println("TC2 == -24056 : " + this.equal( this.TC2, -24056 ));
   }
}
