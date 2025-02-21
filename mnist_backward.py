#coding:utf-8

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
import mnist_forward
import os
import mnist_generateds     #i


BATCH_SIZE = 200    #定义每次输入数据集数量
LEARNING_RATE_BASE = 0.1        #学习率初始值
LEARNING_RATE_DECAY = 0.99      #学习率衰减率
REGULARIZER = 0.0001            #正则化权重
STEPS = 50000
MOVING_AVERAGE_DECAY = 0.99     #滑动平均衰减比较值
MODEL_SAVE_PATH = "./model/"    #模型保存路径
MODEL_NAME = "mnist_model"      #模型保存名称
train_num_examples = 60000  #! 训练总样本数


def backward():

    x = tf.placeholder(tf.float32, [None, mnist_forward.INPUT_NODE])
    y_ = tf.placeholder(tf.float32, [None, mnist_forward.OUTPUT_NODE])
    y = mnist_forward.forward(x, REGULARIZER)
    global_step = tf.Variable(0, trainable=False)

    #定义损失函数
    ce = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=y, labels=tf.argmax(y_, 1))
    cem = tf.reduce_mean(ce)
    loss = cem + tf.add_n(tf.get_collection('losses'))

    #定义衰减学习率
    learning_rate = tf.train.exponential_decay(
            LEARNING_RATE_BASE,
            global_step,
            #mnist.train.num_examples / BATCH_SIZE 
            train_num_examples / BATCH_SIZE,
            LEARNING_RATE_DECAY,
            staircase = True)


    #定义训练过程
    train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss, global_step=global_step)

    #定义滑动平均
    ema = tf.train.ExponentialMovingAverage(MOVING_AVERAGE_DECAY, global_step)
    ema_op = ema.apply(tf.trainable_variables())
    with tf.control_dependencies([train_step, ema_op]):
        train_op = tf.no_op(name='train')

    #定义saver实例
    saver = tf.train.Saver()

    #获取batch_size单位数据集
    img_batch, label_batch = mnist_generateds.get_tfRecord(BATCH_SIZE, isTrain=True)


    #会话
    with tf.Session() as sess:
        init_op = tf.global_variables_initializer()
        sess.run(init_op)
        
        #如果已存在训练的模型,将模型加载到会话中,给所有w和b赋ckpt模型中的值,断点自续,继续训练
        ckpt = tf.train.get_checkpoint_state(MODEL_SAVE_PATH)
        if ckpt and ckpt.model_checkpoint_path:
            saver.restore(sess, ckpt.model_checkpoint_path)

        #加速批处理,使用线程协调器
        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(sess=sess, coord=coord)


        for i in range(STEPS):
            #随机从训练集中抽取 BATCH_SIZE 组数据
            #xs, ys = mnist.train.next_batch(BATCH_SIZE)
            xs, ys = sess.run([img_batch, label_batch])
            _, loss_value, step = sess.run([train_op, loss, global_step], feed_dict={x: xs, y_: ys})
            if i % 1000 == 0:
                print("After %d training steps, loss on training batch is %g." % (step, loss_value))
                #保存模型
                saver.save(sess, os.path.join(MODEL_SAVE_PATH,MODEL_NAME), global_step= global_step)

        #关闭线程协调器
        coord.request_stop()
        coord.join(threads)

def main():
    #mnist = input_data.read_data_sets("./data/", one_hot=True)
    #backward(mnist)
    backward()

if __name__ == '__main__':
    main()
