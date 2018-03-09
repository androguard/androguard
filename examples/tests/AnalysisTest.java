import java.math.BigDecimal;
import java.math.BigInteger;

class AnalysisTest {

    public void testStaticCalls() {
        // this should generate a static call to a method, ie a class reference opcode 0x1c
        System.out.println("Hello world");
    }

    public void testObjectCalls() {
        // Instance of a new object, ie a new instance opcode 0x22
        BigDecimal d = new BigDecimal(23);
    }

    public void testCast(Object foo) {
        // This should generate a check-cast opcode 0x1f
        double x = ((BigInteger) foo).doubleValue();
    }

}