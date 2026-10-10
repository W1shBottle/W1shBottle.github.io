---
title: "Java 学习笔记（五）：重新理解文件读写与自动加载"
date: 2026-10-10T00:00:00+08:00
draft: false
tags: ["Java", "文件读写", "学习笔记"]
ShowToc: true
TocOpen: false
ShowReadingTime: true
---

> 说明：本文围绕学生管理程序的文件读写复习几个基础概念，重点记录 BufferedReader、BufferedWriter 和加载时机中容易混淆的部分。

## 摘要

今天没有继续加功能，主要重新看 `StudentFile`。代码能跟着读，但“谁打开文件、谁处理文字、什么时候加载”还没有完全理顺。

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
writer.write(student.name + "," + student.score);
writer.newLine();
```

学生姓名为张三、成绩为 85 时，先拼接得到 `"张三,85"`，再写出。

两种输出方式也要分清：

```java
System.out.println("张三,85"); // 控制台显示
writer.write("张三,85");      // 通过 writer 写出
```

文件工具并不知道什么是学生，格式是程序自己约定的。

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

**空白行不等于文件末尾。** 空白行返回空字符串 `""`，末尾才返回 `null`。

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

## 7. 现在理解到哪一步

目前能跟着完整流程阅读，文件读写还需要单独练习。准备按下面的顺序巩固：

1. 只读取文件，把每行原样打印。
2. 增加逗号拆分，打印姓名和成绩。
3. 把成绩转成整数，创建学生对象。
4. 最后加回空字段、错误数字和范围校验。

这样每次只增加一部分，能看清到底是哪一步出了问题。昨天提到的 `private` 和 getter 也还需要继续动手验证。
