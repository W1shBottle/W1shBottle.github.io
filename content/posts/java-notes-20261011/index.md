---
description: "给文件加载增加统计，补上删除和自动保存，并通过实际疑问理解异常执行顺序、返回值、路径常量与对象引用。"
title: "Java 学习笔记（六）：加载统计、删除保存与对象返回值"
date: 2026-10-11T00:00:00+08:00
draft: false
tags: ["Java", "文件读写", "面向对象", "学习笔记"]
---

> 说明：本文记录 10 月 11 日围绕学生管理程序完成的练习和讨论。代码中的文件路径使用示例位置；最后的修改成绩重构属于当天讲解的下一步，尚未完成检查。

## 摘要

今天从“成功加载了多少名学生”开始，给加载功能增加成功和跳过计数，接着实现删除、删除确认和删除后自动保存。之后把重复的文件路径提取成常量，再把按姓名查找提取成可以返回 `Student` 的方法。

过程中反复遇到的疑问，其实都和执行顺序有关：异常是谁抛的，`catch` 结束以后去哪，没有删除时是否还会判断保存结果，以及为什么名单里删掉了学生，txt 里却还在。

---

## 1. 统计成功加载和跳过的记录

之前加载结束只输出“学生信息加载完成”，不知道文件里究竟有多少行被接受。先在 `loadStudents()` 打开文件的外层 `try` 前声明两个变量：

```java
int loadedCount = 0;
int skippedCount = 0;
```

它们分别统计本次成功加入集合的学生数，以及因为内容错误而跳过的记录数。声明在外层 `try` 之前，是为了让读取结束后的输出语句也能访问它们，这涉及变量的**作用域**。

成功加入集合之后，才增加成功计数：

```java
students.add(new Student(name, score));
loadedCount++;
```

`loadedCount++` 相当于 `loadedCount = loadedCount + 1`。如果在校验之前就加一，坏数据也会被算进去。

跳过计数放在四种错误情况中：

| 情况 | 增加计数的位置 |
| --- | --- |
| 分割后不是两个字段 | 提示后、`continue` 前 |
| 姓名为空 | 提示后、`continue` 前 |
| 成绩超出 0～100 | 提示后、`continue` 前 |
| 成绩不能转成整数 | `NumberFormatException` 的 `catch` 内 |

例如：

```java
if (score < 0 || score > 100) {
    System.out.println("成绩超出范围，跳过：" + line);
    skippedCount++;
    continue;
}
```

`continue` 会跳过本轮剩下的代码，所以计数要放在它前面。外层的 `IOException` 表示读取文件出问题，不能简单算成一条错误记录，因此不在那个 `catch` 中增加 `skippedCount`。

最后输出：

```java
System.out.println("学生信息加载完成！成功加载 "
        + loadedCount + " 名学生，跳过 "
        + skippedCount + " 条错误记录。");
```

文件中是 `小明,85`、`小红,abc`、`小李,92` 三行时，预期成功加载 2 名学生，跳过 1 条错误记录。

## 2. 没写 throw，NumberFormatException 是哪里来的

加计数时，我又问了一次：这里没有手写 `throw`，为什么会进入 `catch`？

异常来自这一句调用：

```java
int score = Integer.parseInt(parts[1].trim());
```

读到 `小红,abc` 时，实际尝试的是：

```java
Integer.parseInt("abc");
```

`parseInt()` 是 Java 提供的方法，**它内部在转换失败时会抛出 `NumberFormatException`**。不需要我在调用处再写一次 `throw`。

这一次的执行过程是：

```text
parseInt("abc") 转换失败，抛出异常
    ↓
score 没有成功赋值，跳过 try 里剩余的语句
    ↓
匹配的 catch 接住异常，e 指向该异常对象
    ↓
println 输出自己编写的提示，skippedCount 加 1
```

相应的处理代码是：

```java
catch (NumberFormatException e) {
    System.out.println("成绩不是有效整数，跳过：" + line);
    skippedCount++;
}
```

这里没有使用 `e.getMessage()`，打印的是自己拼接的中文提示和原始行。**抛出、捕获、输出是不同步骤，捕获本身不会自动打印文字。**

另一个容易混淆的例子是 `"150"`：它能够转换成整数，所以不会因为超出成绩范围而触发 `NumberFormatException`，而是由后面的 `if` 检查拦住。数值如果连 `int` 的表示范围也超过了，则会转换失败。

## 3. catch 执行完后，程序跳到哪里

今天另一个直接的问题是：执行完 `catch`，会不会回到失败的位置继续？

**`catch` 正常结束后，继续执行整个 `try-catch` 后面的代码，不会回去重试失败的语句，也不会补执行 `try` 中跳过的部分。**

在当前加载方法中，结构是这样的，以下省略了具体校验代码：

```java
while ((line = reader.readLine()) != null) {
    // 拆分当前行、检查字段和姓名……

    try {
        // 转换成绩、检查范围、添加学生……
    } catch (NumberFormatException e) {
        System.out.println("成绩不是有效整数，跳过：" + line);
        skippedCount++;
    }

    // catch 正常结束后来到这里
}
```

这里后面没有其他语句，因此本轮循环结束，回到 `while` 条件，再调用 `reader.readLine()` 读取下一行。

```text
处理小红 → 转换 abc 失败 → catch 输出提示并计数
    ↓
本轮结束 → while 再读一行 → 继续处理小李
```

如果 `try-catch` 后面还有一句“本行处理结束”的输出，就会先执行那一句，再进入下一轮。这个说明以 `catch` 正常执行完为前提；如果里面写了 `return`，则会直接结束方法。

---

## 4. 删除学生：下标、remove 和 return

加载统计完成后，给菜单增加 `9. 删除学生`。先学习三个集合操作：

```java
students.size();    // 学生数量
students.get(i);    // 取出下标为 i 的学生
students.remove(i); // 删除下标为 i 的学生
```

下标从 0 开始。`[小明, 小红, 小李]` 删除下标 1 后变成 `[小明, 小李]`，后面的元素会向前移动，小李的新下标是 1。

最初的删除方法返回 `void`，核心部分是：

```java
for (int i = 0; i < students.size(); i++) {
    Student student = students.get(i);

    if (student.getName().equals(name)) {
        students.remove(i);
        System.out.println("删除成功");
        return;
    }
}

System.out.println("没有找到名为 " + name + " 的学生。");
```

删除后立即 `return`，结束整个方法，避免继续遍历。当前规则是只删除第一个同名学生。

我第一次写的时候漏掉了最后的“没有找到”提示，输入不存在的姓名会直接回到菜单。检查后补上，并理解了它为什么必须在循环外：**只有检查完所有学生，才能确定没有找到。** 找到时已经提前返回，不会误输出这一句。

## 5. 删除之前先确认

之后在真正执行 `remove()` 前加入确认：

```java
System.out.println("确定删除 " + student.getName()
        + " 吗？输入 y 确认，其他输入取消：");

String answer = input.nextLine().trim();

if (!answer.equalsIgnoreCase("y")) {
    System.out.println("已取消删除");
    return;
}
```

这是方法仍返回 `void` 时的片段，下一节改成 `boolean` 后，这里的返回语句也要改。

- `trim()` 去掉输入两端的空白。
- `equalsIgnoreCase("y")` 忽略大小写比较，输入 `y` 或 `Y` 都能确认。
- 前面的 `!` 表示取反，所以不是 `y` 或 `Y` 时进入取消分支。
- 取消时结束方法，后面的删除语句不会执行。

## 6. 名单里删掉了，为什么 txt 里还有

这一步运行后，我遇到了一个很具体的现象：查看所有学生已经没有小明，但打开 txt，小明还在。

原因是当前有两份数据：

| 位置 | 执行 remove 后 |
| --- | --- |
| 内存里的 `students` 集合 | 已经没有小明 |
| 磁盘上的 `students.txt` | 仍是上次保存的内容 |

`students.remove(i)` 只修改集合，没有写文件。查看名单读的也是集合，所以立即能看到变化。选择菜单 8 保存，或者从菜单 0 正常退出并保存成功，文件才会更新。直接点 IDEA 的停止按钮不会执行退出分支。

```text
启动：txt → 读取到集合
添加、修改、删除：操作集合
保存：把集合中的当前名单重新写入 txt
```

目前保存使用默认的覆盖写入：打开成功时清空原内容，再逐个写入当前集合中的学生。集合里没有小明，重新保存时就不会把小明写进去。

## 7. 用 boolean 返回删除结果，再决定是否保存

理解了集合和文件的区别后，下一步是让删除成功后自动保存。

把删除方法的返回类型从 `void` 改成 `boolean`：

```java
static boolean deleteStudent(ArrayList<Student> students, Scanner input)
```

约定结果如下：

| 执行结果 | 返回值 |
| --- | --- |
| 成功从集合删除学生 | `true` |
| 空名单、取消删除、没有找到 | `false` |

所以原来的空名单和取消分支改为 `return false;`，删除成功后改为 `return true;`，最后没找到时也补上 `return false;`。

**`return true` 同时结束方法，并把 `true` 交给调用者。** 它不是输出提示，也不代表文件已经保存。

在 `Main` 中接收结果：

```java
} else if (choice == 9) {
    boolean deleted = StudentService.deleteStudent(students, input);

    if (deleted) {
        boolean saved = StudentFile.saveStudents(students);

        if (!saved) {
            System.out.println("当前名单已删除，但文件未保存成功，请选择 8 重试。");
        }
    }
}
```

这是菜单分支片段。`deleted` 表示集合中是否发生删除，`saved` 表示保存方法是否成功，两个结果要分别判断。

这次保存会写入**整个当前名单**，因此此前尚未保存的添加或修改也会一起保存。当天先给删除接上了自动保存，添加和修改仍保留原来的手动保存或退出保存方式。

### 7.1 没有删除，就没有 saved，后面还会判断吗

我担心过：如果 `deleted` 是 `false`，没有执行保存，下面会不会拿 `saved` 的默认值继续判断？

不会。声明 `saved` 和判断 `!saved` 都在同一个外层 `if` 里面：

```text
deleted 为 false
    ↓
整个 if 代码块跳过
    ↓
不调用保存，不给 saved 赋值，也不判断 !saved
```

只有进入外层 `if`，并且保存调用正常返回后，才会给 `saved` 赋值，再执行后面的判断。

这里的 `saved` 是局部变量，**没有可供直接读取的默认值，使用前必须完成赋值**。下面的写法不能通过编译：

```java
boolean saved;
if (!saved) { // 错误：局部变量尚未初始化
    System.out.println("保存失败");
}
```

而且 `saved` 的作用域只在声明它的代码块内，出了外层大括号就不能使用。

## 8. 为什么保存也会失败

集合操作完成，不意味着硬盘写入一定成功。父文件夹不存在、没有写入权限、磁盘空间不足，或者文件被其他程序独占，都可能导致保存失败。普通编辑器打开 txt 并不一定会阻止写入。

当前代码通过下面的逻辑处理：

```java
catch (IOException e) {
    System.out.println("保存失败：" + e.getMessage());
    return false;
}
```

```text
打开、写入或关闭文件时出现 I/O 异常
    ↓
catch 捕获 IOException
    ↓
e.getMessage() 取出具体原因，println 输出
    ↓
return false → Main 中 saved 为 false → 提醒重试
```

`newBufferedWriter()` 可以创建不存在的文件，但不会自动创建缺失的父文件夹。

还有一个限制需要记住：当前是覆盖写入，如果文件已经被清空、写到一半才失败，旧内容不一定能完整保留。内存中的集合仍然在，解决问题后可以重新保存；当前还没有实现临时文件替换等更可靠的保存方式。

---

## 9. 把重复路径提取成常量

保存、检查是否存在、读取文件，原来各自写了一次路径。为了避免改位置时漏掉一处，把它提取到 `StudentFile` 类中，放在所有方法外面：

```java
private static final Path FILE_PATH =
        Paths.get("D:/java-practice/students.txt");
```

这里是示例绝对路径，实际运行要换成自己已有的文件夹。同时保留 `Paths` 的导入，并增加：

```java
import java.nio.file.Path;
```

| 部分 | 含义 |
| --- | --- |
| `private` | 只在这个类内部使用 |
| `static` | 属于类，现有静态方法可以直接使用 |
| `final` | 初始化后不能再给变量赋另一个值 |
| `Path` | 表示路径的类型 |
| `FILE_PATH` | 常量名，通常用大写和下划线 |
| `Paths.get(...)` | 创建表示路径的对象，本身不打开或创建文件 |

`final` 限制变量重新赋值，**并不是把 txt 设置成只读**，保存仍然可以修改文件内容。

三处使用都要替换：

```java
// 保存：作为 try-with-resources 的资源声明
BufferedWriter writer = Files.newBufferedWriter(
        FILE_PATH, StandardCharsets.UTF_8);

// 判断存在
Files.exists(FILE_PATH);

// 读取：作为 try-with-resources 的资源声明
BufferedReader reader = Files.newBufferedReader(
        FILE_PATH, StandardCharsets.UTF_8);
```

以上只展示路径参数的位置，实际读写仍保留原来的资源块和 `IOException` 处理。我一开始还问了保存方法中的路径是不是不用改，后来明确：**保存处也要改，三处都统一使用常量。** 改完后，整个类只剩常量声明中的一处 `Paths.get(...)`。

## 10. 方法也可以返回 Student

接下来发现查询、修改、删除都在重复按姓名找学生，于是先提取一个只负责查找的方法：

```java
static Student findByName(ArrayList<Student> students, String name) {
    for (Student student : students) {
        if (student.getName().equals(name)) {
            return student;
        }
    }

    return null;
}
```

之前的返回类型有 `void`、`boolean`，这里换成 `Student`，表示返回一个学生对象的引用；找不到则用 `null` 表示没有对象。

`null` 不是空字符串，也不是成绩为 0 的学生。必须遍历完再返回 `null`，不能检查第一个学生没匹配就认定整个集合都没有。

查询方法中改为：

```java
Student student = findByName(students, name);

if (student == null) {
    System.out.println("没有找到名为 " + name + " 的学生。");
    return;
}

System.out.println(student.getName() + "："
        + student.getScore() + "分");
```

先检查有没有找到，再调用对象的方法。`student` 为 `null` 时调用 `getName()` 会抛出 `NullPointerException`。

判断是否为 `null` 使用 `==`，不能写成 `student.equals(null)`，因为后者仍然需要先通过 `student` 调用方法。

查询中的 `boolean found` 和重复的循环可以删掉，查找工作由 `findByName()` 完成。当前遇到同名学生时仍返回第一个匹配对象。

## 11. 下一步：通过返回的引用修改成绩

当天最后讲解了如何让 `updateStudent()` 也调用 `findByName()`。这一步还没有提交修改后的代码进行检查，因此先记下理解和改法，不记成已经完成。

最关键的一点是：**返回的是集合中原来那个对象的引用，没有创建学生副本。**

```text
集合中的某个元素 ──→ 小明这个 Student 对象
                             ↑
局部变量 student ────────────┘
```

因此，查找成功并确认不是 `null` 后：

```java
student.setScore(newScore);
```

修改的就是集合中那个学生。查看全部学生时可以看到新成绩，不需要再调用 `students.add(student)`；再次添加反而会让集合多出一个指向同一对象的元素。

还讲到了把成绩重输的循环写得更直接：

```java
while (newScore < 0 || newScore > 100) {
    System.out.println("成绩必须在 0 到 100 之间，请重新输入：");
    newScore = InputUtils.readInt(input);
}
```

条件不合法就继续输入，合法后条件变为 `false`，自然离开循环。这与原来的 `while (true)` 配合条件判断和 `break` 实现的行为一致。

## 12. 当天完成情况与还要练习的地方

| 内容 | 当天进度 |
| --- | --- |
| 加载成功和跳过计数 | 已完成并检查，源文件编译通过 |
| 删除学生与菜单入口 | 已完成；最初缺少没找到的提示，后来补上 |
| 删除确认、返回删除结果、删除后自动保存 | 已完成并检查代码 |
| 提取路径常量，替换三处使用 | 已完成并检查，源文件编译通过 |
| `findByName()` 与查询功能复用 | 已完成并检查，源文件编译通过 |
| 修改成绩复用查找方法 | 已讲解，尚待修改后检查 |

删除功能的初版还做过独立运行验证，覆盖首个、中间、最后一个元素、不存在的姓名、输入两端空白、重名和空名单七种情况，并检查删除后查看和查询仍能运行。这些验证没有通过运行主程序去覆盖实际存档，也不能当成后续自动保存所有分支的完整测试。

接下来需要自己继续验证：修改成绩后人数不变；查找失败时不访问空引用；确认删除才保存，取消不保存。文件读写也还需要从头独立写一次，把“文件中的文字”和“内存中的对象”真正对应起来。

今天最需要反复练习的是沿着代码看执行路径：进入哪个分支、在哪里结束方法、返回了什么，以及这一步改变的是集合还是文件。
