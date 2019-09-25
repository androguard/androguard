public class FieldsTest {

    public String afield = "hello world";
    private String bfield = "sdf";

    public static String cfield = "i am static";

    public void foonbar() {
        System.out.println(this.afield);
        System.out.println(this.bfield);

        this.afield = "hello mars";

        System.out.println(this.afield);
        System.out.println(cfield);
    }

}
