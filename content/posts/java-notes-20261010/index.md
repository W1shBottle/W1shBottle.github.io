---
description: "从文件加载时的异常提示，到 private、getter/setter 和成绩范围校验，继续整理学生管理程序。"
title: "Java 学习笔记（五）：文件读写、自动加载与对象封装"
date: 2026-10-10T00:00:00+08:00
draft: false
tags: ["Java", "文件读写", "面向对象", "学习笔记"]
ShowToc: true
TocOpen: false
ShowReadingTime: true
---

> 说明：本文围绕学生管理程序，记录文件读写、异常提示和对象封装中实际遇到的问题，以及当天完成的修改与验证。

## 摘要

今天先重新看 `StudentFile`，把“谁打开文件、谁处理文字、什么时候加载”串起来。之后从一次没有注意到的错误提示，继续理解程序执行顺序，再给 `Student` 加上私有字段、getter/setter 和成绩范围检查。

这次主要在完善已有功能。能读懂代码之后，还需要自己修改、运行，确认程序的行为和理解一致。

---

## 1. 没有加载选项，load 是不是没实现

这是今天最直接的疑问。菜单里有保存，却没有加载，于是以为加载功能还缺一个入口。

实际在 `main` 方法开头已经写了：

```java
ArrayList<Student> students = new ArrayList<>();
StudentFile.loadStudents(students);
```

这两句在菜单循环之前，因此流程是：

```text
启动 → 创建空名单 → 从文件加载 → 显示菜单 → 接收 choice
```

**菜单决定后续交互，启动时需要做的事情可以直接执行。** 所以不需要为每个方法都增加选项。

当前 `loadStudents()` 通过 `add()` 向名单追加学生。如果直接反复调用，会产生重复记录，暂时保持启动时加载一次。

---

## 2. BufferedWriter 是什么

可以和已经用过的 `Scanner` 对照：

| 类型 | 主要用途 |
| --- | --- |
| `Scanner` | 读取和解析输入 |
| `BufferedWriter` | 带缓冲的字符写入 |
| `BufferedReader` | 带缓冲的字符读取 |

`writer`、`reader` 是自己起的变量名。真正提供功能的是它们所引用的对象。

### 2.1 Buffered 的意思

缓冲区是一块暂存内容的内存。调用 `write()` 时，文字可能先进入缓冲区，再集中写到底层目标，减少频繁写入。

关闭 writer 时，会尝试写出剩余缓冲内容。写入或关闭都有可能失败，所以成功提示应放在整个资源块正常结束之后。

## 3. 创建写入工具的一句代码，拆开看

```java
try (BufferedWriter writer = Files.newBufferedWriter(
        Paths.get("students.txt"),
        StandardCharsets.UTF_8)) {
    // 写入文字
}
```

这里展示资源块结构，完整方法还需要捕获或声明 `IOException`。

### 3.1 Paths.get(...)

得到一个表示文件位置的 `Path` 对象，**本身不会创建文件**。

示例中的 `students.txt` 是相对路径，以程序工作目录为基准，并不保证与源码同目录。

### 3.2 StandardCharsets.UTF_8

指定 UTF-8 编码。文件保存的是字节，编码规定文字与字节怎样转换。读写使用一致的编码，才能正确还原中文。

### 3.3 Files.newBufferedWriter(...)

打开写入工具，并把返回的对象交给变量 `writer`。

当前不额外传入打开选项时，文件不存在会创建，存在则清空后写入。所以每次保存的是当前完整名单。

### 3.4 try 后面的括号

这是 **try-with-resources**，离开代码块时自动关闭资源，包括发生异常的情况。不需要再手动写 `writer.close()`。

---

## 4. 写入文件的是文字，不是 Student 对象本身

```java
writer.write(student.getName() + "," + student.getScore());
writer.newLine();
```

学生姓名为张三、成绩为 85 时，先拼接得到 `"张三,85"`，再写出。

两种输出方式也要分清：

```java
System.out.println("张三,85"); // 控制台显示
writer.write("张三,85");      // 通过 writer 写出
```

文件工具并不知道什么是学生，格式是程序自己约定的。这里使用的是完成封装后的 getter，后面再记录这部分修改。

## 5. BufferedReader 每次读到什么

核心方法是：

```java
reader.readLine()
```

每次读取下一行，不包含行末换行符。假设文件内容是：

```text
张三,85
李四,90
```

| 调用次数 | 返回结果 |
| --- | --- |
| 第一次 | `"张三,85"` |
| 第二次 | `"李四,90"` |
| 第三次 | `null`，文件已读完 |

**空行不等于文件末尾。** 没有字符的空行返回空字符串 `""`，只包含空格的行会保留空格，末尾才返回 `null`。

读出来以后，再由程序拆分、转换和校验：

```text
"张三,85" → "张三" 与 "85" → 姓名和整数成绩 → Student 对象
```

---

## 6. loadStudents 返回 void，为什么名单会变

这里以前容易忽略：方法虽然没有返回列表，但拿到的引用指向 `Main` 创建的同一个列表对象。

```java
students.add(new Student(name, score));
```

这句操作的就是那个列表，所以方法结束后，`Main` 中也能看到新加入的学生。

Java 传递的是**引用值的副本**，并没有把整个列表复制一份。通过这个引用修改对象，与给局部变量重新赋值，是不同的操作。

## 7. 成绩不是有效整数，这句提示什么时候出现

看到下面这段代码时，我不确定 `catch` 里的提示到底什么时候执行：

```java
try {
    int score = Integer.parseInt(parts[1].trim());

    if (score < 0 || score > 100) {
        System.out.println("成绩超出范围，跳过：" + line);
        continue;
    }

    students.add(new Student(name, score));
} catch (NumberFormatException e) {
    System.out.println("成绩不是有效整数，跳过：" + line);
}
```

这段代码位于逐行读取的循环中。`Integer.parseInt()` 尝试把文本转换成 `int`，转换不了时会抛出 `NumberFormatException`，跳过 `try` 中剩余的语句，进入对应的 `catch`。

| 文件中的一行 | 处理结果 |
| --- | --- |
| `小明,85` | 转换成功，成绩合法，加入名单 |
| `小红,abc` | 不能转成整数，进入 `catch` |
| `小李,85.5` | 不能按整数解析，进入 `catch` |
| `小王,` | 成绩是空字符串，进入 `catch` |
| `小张,150` | 能转成整数，但范围不合法，执行 `if` 中的提示 |

**能否转换成整数，与成绩是否在 0～100 之间，是两道检查。** 即使文本只包含数字，数值超出 `int` 能表示的范围，也会转换失败。

这里的 `line` 是完整的一行，所以提示会同时带上姓名和原始成绩。处理完当前行的异常后，循环继续读取下一行。

### 7.1 提示原来就在控制台第一行

我把文件改成：

```text
小明,85
小红,abc
小李,92
```

最初以为没有输出错误提示，后来才发现，它在程序刚启动时就已经显示了：

```text
成绩不是有效整数，跳过：小红,abc
学生信息加载完成！

1. 添加学生
...
```

原因还是执行顺序：先调用 `loadStudents()`，然后才进入菜单循环。提示使用 `System.out.println()`，显示在 IDEA 的运行控制台，不会写回 `students.txt`。

另外，当前程序只在启动时读一次文件。程序已经运行后再修改 txt，不会自动触发加载。

---

## 8. 生成 getter/setter，还不等于完成封装

接下来把注意力转到 `Student`。原来的字段没有访问修饰符，同一包中的其他类可以直接读取和修改：

```java
String name;
int score;
```

我先用 IDEA 生成了 getter 和 setter，但漏掉了字段上的 `private`。这样方法虽然有了，其他类仍然能绕过它们直接赋值。

改成下面这样，外部访问才会受到限制：

```java
private String name;
private int score;

public String getName() {
    return name;
}

public int getScore() {
    return score;
}
```

`private` 表示字段只能在本类内部直接访问；`public` 方法则提供对外的访问入口。getter 返回当前对象的数据，所以这里不加 `static`。

其他文件中的调用也要一起修改：

| 原写法 | 修改后 |
| --- | --- |
| `student.name` | `student.getName()` |
| `student.score`，读取成绩 | `student.getScore()` |
| `student.score = newScore;` | `student.setScore(newScore);` |
| `students.get(0).score` | `students.get(0).getScore()` |

不仅是显示名单，计算平均分、查找姓名、修改成绩、查询最高分和保存文件，都要检查是否还有直接访问字段的地方。

`Student` 内部的 `this.name = name;` 仍然可以使用。左边是当前对象的字段，右边是传进来的参数。

### 8.1 顺手记下两个 IDEA 操作

Windows 默认键位下：

- 光标放在类内部、方法外部，按 `Alt + Insert`，可以生成 getter、setter 和构造方法。参见 [IDEA 生成代码说明](https://www.jetbrains.com/zh-cn/help/idea/generating-code.html)。
- 按住 `Alt + Shift`，用鼠标左键点击其他位置，可以添加多个光标，一次给多行加上 `private `；按 `Esc` 恢复单个光标。参见 [IDEA 多光标说明](https://www.jetbrains.com/help/idea/multicursor.html)。

方法按实际需要生成即可，不是每个字段都必须同时有 getter 和 setter。当前保留了生成的 `setName()`，但菜单还没有修改姓名的入口。

## 9. setter 不能只有赋值

IDEA 自动生成的代码是：

```java
public void setScore(int score) {
    this.score = score;
}
```

它只负责赋值，调用 `setScore(999)` 仍然会把成绩改成 999。下一步是在赋值之前检查：

```java
public void setScore(int score) {
    if (score < 0 || score > 100) {
        throw new IllegalArgumentException("成绩必须在 0 到 100 之间！");
    }

    this.score = score;
}
```

- `||` 表示“或者”，小于 0 或大于 100 都不合法，0 和 100 则可以通过。
- `new IllegalArgumentException(...)` 创建一个表示参数不合法的异常对象。
- `throw` 抛出异常，当前方法不会继续执行后面的赋值语句。
- 只有通过检查，才把参数 `score` 保存到当前对象的 `this.score`。

`IllegalArgumentException` 是 Java 自带的异常类，不需要额外导入。

### 9.1 构造方法也不能绕过检查

如果构造方法仍然直接写 `this.score = score;`，创建对象时还是可以放进不合法成绩。因此也改为调用 setter：

```java
Student(String name, int score) {
    this.name = name;
    setScore(score);
}
```

这里的 `setScore(score)` 等价于 `this.setScore(score)`，调用的是当前对象的方法。这样无论创建学生，还是修改已有学生的成绩，都会经过同一处校验。

## 10. throw 和打印提示不是一回事

这里之前只记住了“成绩不合法就抛异常”，但没有把谁抛出、谁捕获、谁输出连起来。完整的过程应该是：**方法内部通过 `throw` 抛出异常，调用处匹配的 `catch` 捕获异常，再由里面的打印语句输出提示。**

### 10.1 方法里：创建异常对象，再抛出去

在 `Student` 类的 `setScore()` 中：

```java
public void setScore(int score) {
    if (score < 0 || score > 100) {
        // 创建异常对象，附上原因，再把异常抛出去
        throw new IllegalArgumentException("成绩必须在 0 到 100 之间！");
    }

    this.score = score;
}
```

`new IllegalArgumentException(...)` 创建了一个异常对象，括号里的文字是它携带的详细信息。**这一步把信息放进异常对象，并没有输出到控制台。**

`throw` 把异常抛出去。这个方法内部没有相应的 `catch`，异常就沿着方法调用关系向外传播，寻找能够处理它的代码。当前方法不会继续执行 `this.score = score;`，因此非法成绩不会覆盖原成绩。

### 10.2 调用处：catch 接住异常，e 指向这个对象

下面是一段独立演示，说明调用者怎样接住异常，不代表目前菜单里已经加入了这段 `try-catch`：

```java
Student student = new Student("小明", 85);

try {
    student.setScore(150); // 进入方法后，发现 150 不合法，抛出异常
    System.out.println("修改成功！"); // 本次不会执行
} catch (IllegalArgumentException e) {
    // 捕获上面抛出的异常，再取出文字并打印
    System.out.println(e.getMessage());
}

System.out.println(student.getScore()); // 异常处理完，继续执行这里
```

`catch (IllegalArgumentException e)` 可以拆开看：

- `IllegalArgumentException`：这里能够捕获的异常类型，也能捕获它的子类异常。
- `e`：异常变量，指向这次被捕获的异常对象。它不是提示文字本身，名字也不一定非要叫 `e`。
- 大括号里的代码：匹配到异常后执行的处理逻辑。

执行 `student.setScore(150)` 时，异常先从方法内部传回这个调用位置，再由对应的 `catch` 捕获。`try` 中剩下的“修改成功”不会执行。

### 10.3 输出时：先取出信息，再打印

这一句其实包含两步：

```java
System.out.println(e.getMessage());
```

拆开可以写成：

```java
String message = e.getMessage(); // 取出创建异常时附上的提示文字
System.out.println(message);    // 把这段文字输出到控制台
```

所以前面的完整演示输出为：

```text
成绩必须在 0 到 100 之间！
85
```

整个过程串起来就是：

```text
调用 student.setScore(150)
    ↓
方法内检查出 150 不合法
    ↓
new 创建异常对象，保存提示文字
    ↓
throw 抛出异常，跳过后面的成绩赋值
    ↓
调用处的 try 不再往下执行，进入匹配的 catch
    ↓
异常变量 e 指向被捕获的异常对象
    ↓
e.getMessage() 取出提示文字
    ↓
System.out.println(...) 输出到控制台
    ↓
catch 正常结束，继续执行后面的代码，读到原成绩 85
```

**`throw` 负责抛出，`catch` 负责捕获，`getMessage()` 负责取出信息，`println()` 才负责输出。** 捕获异常本身不会自动打印提示，也不会自动重新执行失败的语句。

这个例子里，`catch` 正常执行结束，程序才会继续到后面的打印语句。如果异常一直没有被捕获，它会继续向外传播；在当前这个单线程控制台程序中，最终会导致程序结束，并由运行时报告未捕获的异常。

### 10.4 读取文件时，异常是谁抛出的

文件里写着 `小红,abc` 时，调用的是：

```java
Integer.parseInt("abc");
```

虽然我没有在这里手写 `throw`，但 `Integer.parseInt()` 内部会在转换失败时抛出 `NumberFormatException`。它随后被加载方法中的这一段捕获：

```java
catch (NumberFormatException e) {
    System.out.println("成绩不是有效整数，跳过：" + line);
}
```

和成绩 setter 的演示相比，这里有两个区别：

| 对比项 | 成绩 setter | 文件里的错误数字 |
| --- | --- | --- |
| 谁抛出异常 | 自己在 `setScore()` 中写的 `throw` | `Integer.parseInt()` 方法内部 |
| 抛出的类型 | `IllegalArgumentException` | `NumberFormatException` |
| 示例中打印的内容 | 用 `e.getMessage()` 取出的异常信息 | 自己拼接的中文提示加上原始行 `line` |

因此，这段 `catch` 虽然用 `e` 接住了异常，但并没有读取 `e.getMessage()`，而是选择输出自己写的提示。这两种写法都可以，取决于希望给使用者展示什么信息。

### 10.5 当前程序中的检查仍然保留

目前菜单和文件读取中的范围检查仍然保留：菜单负责提示和重新输入，读取文件时负责跳过坏记录，`Student` 自己也保证成绩合法。因此，从当前菜单正常操作时，不合法成绩通常已经被前面的 `if` 拦住，不会走到 setter 抛异常的地方。

另外，`catch` 需要匹配异常类型。加载方法里的 `catch (NumberFormatException e)` 不会捕获 `new IllegalArgumentException(...)` 创建的异常；当前文件加载中的范围检查会提前跳过这类不合法记录。如果以后改变检查方式，也要一起考虑调用处应该捕获什么异常。

---

## 11. 这次改完后验证了什么

五个 Java 源文件编译通过，并在独立检查中验证了创建对象和修改成绩的行为，没有通过运行退出保存流程去覆盖现有存档。

| 验证内容 | 结果 |
| --- | --- |
| 创建学生时分别传入 0、85、100 | 正常保存成绩 |
| 将已有学生的成绩分别设为 0、85、100 | 正常修改 |
| 创建学生时传入 -1、101 | 抛出异常 |
| 将 85 分改为 -1、101 | 抛出异常，原成绩仍为 85 |

这十项检查全部通过。到这里，成绩字段的封装和范围校验已经接上了，但姓名的非空等规则还没有加入 `Student`，不能据此认为所有数据都已经完整校验。

## 12. 还需要继续练习的地方

文件读写现在能跟着流程解释，但还需要自己从头写一次，把“读一行、拆分、转换、校验、加入名单”串起来。

另外还讨论了统计加载人数：在外层读取 `try` 前声明 `int loadedCount = 0;`，只在成功 `add()` 后执行 `loadedCount++`，最后输出结果。变量放在 `try` 外，是为了让后面的打印语句也能访问它。这项练习还没有加进当前代码。

今天最有帮助的两点是：错误提示出现在哪里，要沿着程序执行顺序找；字段加了 `private` 之后，还要在方法里落实规则，才能真正保护对象的数据。
