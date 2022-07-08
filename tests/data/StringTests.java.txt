public class StringTests{
    public static void main(String... args){
    
        String a = "this is a quite normal string";
        String b = "\u0000 \u0001 \u1234";
        String c = "使用在線工具將字符串翻譯為中文";
        String d = "перевод строки на русский с помощью онлайн-инструментов";
        String e = "온라인 도구를 사용하여 문자열을 한국어로 번역";
        String f = "オンラインツールを使用して文字列を日本語に翻訳";
        String g = "This is \ud83d\ude4f, an emoji.";
        String h = "\u2713 check this string";
        String i = "\uFFFF \u0000 \uFF00";
        String j = "\u0420\u043e\u0441\u0441\u0438\u044f";

        System.out.println(a);
        System.out.println(b);
        System.out.println(c);
        System.out.println(d);
        System.out.println(d);
        System.out.println(f);
        System.out.println(g);
        System.out.println(h);
        System.out.println(i);
        System.out.println(j);
    }

}
