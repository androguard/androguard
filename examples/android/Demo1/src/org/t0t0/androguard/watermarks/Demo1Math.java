package org.t0t0.androguard.watermarks;                                                                                                                                                                                           

public class Demo1Math {
   
    /* RC4 */ 
    private byte state[] = new byte[256];
    private int x, y;
    public void RC4(String key) throws NullPointerException {
        this.RC4(key.getBytes());
    }

    public void RC4(byte[] key) throws NullPointerException {
        for (int i=0; i < 256; i++) {
            state[i] = (byte)i;
        }
        
        int index1 = 0;
        int index2 = 0;
        
        byte tmp;
        
        if (key == null || key.length == 0) {
            throw new NullPointerException();
        }
        
        for (int i=0; i < 256; i++) {

            index2 = ((key[index1] & 0xff) + (state[i] & 0xff) + index2) & 0xff;

            tmp = state[i];
            state[i] = state[index2];
            state[index2] = tmp;
            
            index1 = (index1 + 1) % key.length;
        }
    }

    public byte[] rc4(String data) {
        if (data == null) {
            return null;
        }
        
        byte[] tmp = data.getBytes();
        
        this.rc4(tmp);
        
        return tmp;
    }
    
    public byte[] rc4(byte[] buf) {
        int xorIndex;
        byte tmp;
        
        if (buf == null) {
            return null;
        }
        
        byte[] result = new byte[buf.length];
        
        for (int i=0; i < buf.length; i++) {

            x = (x + 1) & 0xff;
            y = ((state[x] & 0xff) + y) & 0xff;

            tmp = state[x];
            state[x] = state[y];
            state[y] = tmp;
            
            xorIndex = ((state[x] &0xff) + (state[y] & 0xff)) & 0xff;
            result[i] = (byte)(buf[i] ^ state[xorIndex]);
        }
        return result;
    }
}
