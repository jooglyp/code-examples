from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import argparse
import sys
import numpy as np
import pdb

NUM_HIDDEN_NODES = 10
LEARNING_RATE = .01
NUM_TRAINING_LOOPS = 10000
NUM_PER_BATCH = 50
NUM_TEST_BATCH = 100
L_ENDPOINT = -np.pi
R_ENDPOINT = np.pi


def ann(x,NUM_HIDDEN_NODES):
  
  input_dim = 1
  output_dim = 1

  W = tf.get_variable("W",[input_dim,NUM_HIDDEN_NODES])
  b = tf.get_variable("b",[NUM_HIDDEN_NODES])
  U = tf.get_variable("U",[NUM_HIDDEN_NODES, output_dim])
  c = tf.get_variable("c",[output_dim])

  a = tf.sigmoid(tf.matmul(x,W) + b)

  y_model = tf.matmul(a,U) + c

  return y_model

def main(_):  
  x = tf.placeholder(tf.float32, shape = [None, 1])
  
  y_model = ann(x,NUM_HIDDEN_NODES)

  y_true = tf.placeholder(tf.float32, shape = [None, 1])

  loss = tf.reduce_mean(tf.square(y_model - y_true))

  with tf.name_scope('adam_optimizer'):
    train_step = tf.train.AdamOptimizer(LEARNING_RATE).minimize(loss)

  with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    for i in range(NUM_TRAINING_LOOPS):
      x_train = np.random.uniform(L_ENDPOINT,R_ENDPOINT,[NUM_PER_BATCH,1]).astype(np.float32)
      batch = [x_train,np.sin(x_train)]
      if i % 100 == 0:
        train_loss = loss.eval(feed_dict={x: batch[0], y_true: batch[1]})
        print('step %d, training loss %g' % (i, train_loss))
      train_step.run(feed_dict={x: batch[0], y_true: batch[1]})

    # construct some test data
    x_test = np.random.uniform(L_ENDPOINT,R_ENDPOINT,[NUM_TEST_BATCH,1])
    y_test = np.sin(x_test)
    

    print('test  loss %g' % loss.eval(feed_dict={
        x: x_test, y_true: y_test}))


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--data_dir', type=str, default='/tmp/tensorflow/mnist/input_data',
                      help='Directory for storing input data')
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
