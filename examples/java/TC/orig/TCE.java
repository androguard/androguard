public class TCE {
   public int TC1 = 1337;
   private int TC2 = -90000;

   public String equal(int a, String b)
   {
      String c = Integer.toString( a );

      System.out.print(c + " " + b + " ---- ");
      if (c.equals(b)) {
         return "True";
      }

      return "False";
   }

   public TCE()
   {
      System.out.println("TCE TC1 == 1337 : " + this.equal( this.TC1, "1337" ));
      System.out.println("TCE TC2 == -90000 : " + this.equal( this.TC2, "-90000" ));
      TC1 = 20;
      System.out.println("TCE TC1 == 20 : " + this.equal( this.TC1, "20" ));
   
      TCC c = new TCC();
      c.T1();
   }

   public void T1()
   {
   }
}
