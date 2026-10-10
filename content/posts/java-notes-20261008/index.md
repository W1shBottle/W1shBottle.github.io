---
title: "Java 学习笔记（三）：异常处理与文件保存"
date: 2026-10-08T00:00:00+08:00
draft: false
tags: ["Java", "异常处理", "文件读写"]
ShowToc: true
TocOpen: false
ShowReadingTime: true
---

> 说明：本文记录整数输入重试和文本文件保存的学习过程。代码片段按当日练习阶段整理，文件路径统一使用示例写法。

## 摘要

今天处理了两件事：输入字母时让程序继续运行，以及把学生名单写入文件。重点是 **`try-catch`、循环重试、输入清理和资源关闭**。

---

## 1. nextInt() 为什么会报错

```java
int score = input.nextInt();
```

这句期待读取一个整数。输入 `abc` 或 `2.5` 时，会出现 `InputMismatchException`。

`try-catch` 可以捕获指定异常，但捕获以后不会自动重新读取。想重试，还需要循环。

## 2. 提取一个读取整数的方法

下面是当天放在 `Main` 类中的版本，使用类里已有的 `Scanner input`：

```java
static int readInt() {
    while (true) {
        try {
            int num = input.nextInt();
            input.nextLine();
            return num;
        } catch (InputMismatchException e) {
            System.out.println("输入错误，请输入整数。");
            input.nextLine();
        }
    }
}
```

### 2.1 两个 nextLine() 的作用

| 位置 | 作用 |
| --- | --- |
| 成功读取整数后 | 消耗本行剩余内容和换行符 |
| 捕获输入异常后 | 丢弃错误输入，准备下一次读取 |

失败时如果不清理，下一轮可能仍然读到同一段错误内容，一直重复报错。

### 2.2 return 不只是返回一个值

```java
return num;
```

它会把整数交给调用者，并结束整个方法，包括里面的循环。因此成功后不需要再写 `break`。

### 2.3 类型检查和范围检查

`readInt()` 能保证读到整数，但 `101` 也是整数。

所以成绩是否在 `0—100` 之间，还需要单独判断。这两个检查负责不同问题。

---

## 3. 替换代码时踩的坑

第一处很直接：`newScore = readInt()` 后漏了分号，编译不通过。

第二处更容易忽略：原来的代码在读取成绩后调用了一次 `nextLine()`，换成 `readInt()` 后没有删掉它。

新方法内部已经消耗了换行，外面再读一次，就会等待额外一行输入，看起来像卡住了。

> 记忆点：封装方法时，不只要复制核心操作，还要检查调用处有没有重复处理。

修正后，菜单和成绩输入都能在输错后继续重试。修改成绩时输入 `abc → 101 → 85`，分别处理类型错误和范围错误，最后保存 85。

---

## 4. 把学生名单保存成文字

暂时约定每行一个学生：

```text
张三,85
李四,92
```

姓名中先不使用英文逗号。这只是练习用的简单文本格式，不是完整的 CSV 解析方案。

保存的核心代码是：

```java
try (BufferedWriter writer = Files.newBufferedWriter(
        Paths.get("students.txt"),
        StandardCharsets.UTF_8)) {

    for (Student student : students) {
        writer.write(student.name + "," + student.score);
        writer.newLine();
    }

} catch (IOException e) {
    System.out.println("保存失败：" + e.getMessage());
}
```

`writer.write(...)` 写文字，`writer.newLine()` 换行。外面的 `try (...)` 会在离开代码块时自动关闭资源。

本例采用覆盖写入：保存的是当前完整名单，如果每次都追加整份名单，就会出现重复学生。

## 5. 文件保存在哪里

我原来以为文件会自动放到源码旁边，这里需要区分：

- **相对路径**：相对于程序的工作目录。
- **绝对路径**：指定固定位置，移动项目后可能需要修改。

上面的 `students.txt` 使用相对路径，所以它不一定与 `.java` 文件在同一个目录。

---

## 6. 开始接触读取，但还没熟悉

保存的反向过程是：

```text
读取文字 → 拆分姓名和成绩 → 成绩转为整数 → 创建学生对象
```

今天接触了 `BufferedReader`、`readLine()`、`split()` 和 `Integer.parseInt()`，并学习在菜单循环前加载一次名单。

文件读写涉及的类和方法一下子多了起来，还需要拆开练。下一步继续处理保存结果，以及存档中出现错误内容时怎么办。
